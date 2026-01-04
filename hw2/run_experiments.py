#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pydicom
from skimage.metrics import structural_similarity as ssim
from skimage.filters import sobel

from src.bitstream import BitStreamWriter
from src.codec import MedicalCodec


def iter_files(root: str):
    root_path = Path(root)
    if root_path.is_file():
        yield str(root_path)
        return
    for p in root_path.rglob('*'):
        if not p.is_file():
            continue
        # Dataset A has files without extension; accept all files.
        if p.name == 'DICOMDIR' or p.name.startswith('.'):
            continue
        yield str(p)


def _display_file_id(fpath: str, data_root: str) -> str:
    root_path = Path(data_root)
    try:
        fp = Path(fpath)
        if root_path.is_dir():
            return str(fp.relative_to(root_path))
    except Exception:
        pass
    return os.path.basename(fpath)


def extract_bit_depth_info(ds, img: np.ndarray):
    bits_stored = int(ds.get('BitsStored', 16))
    pixel_representation = int(ds.get('PixelRepresentation', 1))
    if bits_stored < 1 or bits_stored > 16:
        bits_stored = 16
    if pixel_representation not in (0, 1):
        pixel_representation = 1
    if ds.get('BitsStored', None) is None:
        bits_stored = 16 if img.dtype in (np.uint16, np.int16) else 8
    if ds.get('PixelRepresentation', None) is None:
        pixel_representation = 0 if img.dtype == np.uint16 else 1
    return bits_stored, pixel_representation


def compute_ssim_metrics(original: np.ndarray, recon: np.ndarray, *, bits_stored: int):
    max_val = float((1 << int(bits_stored)) - 1)
    ssim_val = float(ssim(original, recon, data_range=max_val))

    # Task-based proxy: edge-map similarity
    edge_orig = sobel(original.astype(np.float32))
    edge_recon = sobel(recon.astype(np.float32))
    max_edge = float(np.max(edge_orig))
    if max_edge <= 0:
        edge_ssim = 1.0
    else:
        edge_ssim = float(ssim(edge_orig, edge_recon, data_range=max_edge))
    return ssim_val, edge_ssim


def write_error_map(output_path: str, original: np.ndarray, recon: np.ndarray, *, bits_stored: int):
    # absolute error in image domain
    err = np.abs(original.astype(np.int32) - recon.astype(np.int32)).astype(np.uint16)

    # Save a true-valued 16-bit TIFF for analysis
    import tifffile
    tifffile.imwrite(output_path + '_abs_error.tiff', err)

    # Save a viewable visualization (8-bit) scaled for visibility
    # NOTE: Using the theoretical full-scale (2^B-1) often produces nearly-black images
    # when the actual error occupies a small fraction of that range. Use a robust
    # percentile-based window for human-visible visualization.
    p = float(np.percentile(err, 99))
    if not np.isfinite(p) or p <= 0:
        p = float(np.max(err))
    if not np.isfinite(p) or p <= 0:
        p = 1.0
    vis = (np.clip(err.astype(np.float32) / p, 0.0, 1.0) * 255.0).astype(np.uint8)
    import imageio.v3 as iio
    iio.imwrite(output_path + '_abs_error_vis.png', vis)


def write_recon_vis(output_path: str, recon: np.ndarray):
    recon_f = recon.astype(np.float32)
    lo, hi = np.percentile(recon_f, [1, 99])
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        lo, hi = float(np.min(recon_f)), float(np.max(recon_f))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        lo, hi = 0.0, 1.0
    vis = (np.clip((recon_f - lo) / (hi - lo + 1e-6), 0.0, 1.0) * 255.0).astype(np.uint8)
    import imageio.v3 as iio
    iio.imwrite(output_path + '_recon_vis.png', vis)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', required=True, help='DICOM slice file or directory (recursively scanned)')
    parser.add_argument('--output_dir', default='results/experiments', help='Where to write recon/error/csv')
    parser.add_argument('--qualities', type=int, nargs='+', default=[30, 50, 80], help='Three operating points')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of images')
    parser.add_argument('--write_bitstreams', action='store_true', help='Write .medc files for each image/quality (can be large)')
    parser.add_argument('--save_images_limit', type=int, default=5, help='Save recon/error maps for the first N images (per dataset)')
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []

    header_len = int(
        __import__('struct').calcsize('>4sBHHBfBBHHHH')
    )

    saved_images = 0
    img_index = 0
    for fpath in iter_files(args.data_dir):
        if args.limit is not None and img_index >= args.limit:
            break
        try:
            ds = pydicom.dcmread(fpath, force=True)
            if not hasattr(ds, 'pixel_array'):
                continue
            img = ds.pixel_array
            if img.ndim != 2:
                continue

            bits_stored, pixel_representation = extract_bit_depth_info(ds, img)
            if img.dtype not in (np.uint16, np.int16):
                img = img.astype(np.int16)

            original_size = img.nbytes

            for q in args.qualities:
                codec = MedicalCodec(quality=q)
                stream, h, w = codec.encode(img)

                roi = (0, 0, 0, 0)
                bs, pr = int(bits_stored), int(pixel_representation)

                if args.write_bitstreams:
                    bitstream_path = out_dir / f'img{img_index:05d}_q{q}.medc'
                    writer = BitStreamWriter(str(bitstream_path))
                    writer.write_header(
                        h,
                        w,
                        q,
                        codec.scale,
                        bits_stored=bs,
                        pixel_representation=pr,
                        roi=None,
                    )
                    writer.write_block_data(stream)
                    writer.close()
                    compressed_size = int(bitstream_path.stat().st_size)
                else:
                    payload_len = int(len(stream) * 4)
                    compressed_size = int(header_len + 4 + payload_len)

                # Ablation: estimate size without RLE (store all quantized coefficients)
                pad_h = (8 - h % 8) % 8
                pad_w = (8 - w % 8) % 8
                full_h, full_w = h + pad_h, w + pad_w
                n_blocks = (full_h // 8) * (full_w // 8)
                payload_len_no_rle = int(n_blocks * 64 * 4)
                compressed_size_no_rle = int(header_len + 4 + payload_len_no_rle)

                recon = codec.decode(
                    stream,
                    h,
                    w,
                    scale_factor_override=codec.scale,
                    roi=roi,
                    bits_stored=bs,
                    pixel_representation=pr,
                )

                max_val = float((1 << int(bs)) - 1)
                mse = float(np.mean((img.astype(np.float64) - recon.astype(np.float64)) ** 2))
                rmse = float(np.sqrt(mse))
                psnr = float('inf') if mse == 0 else float(20 * np.log10(max_val / rmse))
                cr = float(original_size / compressed_size) if compressed_size > 0 else 0.0
                bpp = float((compressed_size * 8) / (h * w)) if (h > 0 and w > 0) else 0.0

                ssim_val, edge_ssim = compute_ssim_metrics(img, recon, bits_stored=bs)

                cr_no_rle = float(original_size / compressed_size_no_rle) if compressed_size_no_rle > 0 else 0.0
                bpp_no_rle = float((compressed_size_no_rle * 8) / (h * w)) if (h > 0 and w > 0) else 0.0
                rle_savings = float(1.0 - (compressed_size / compressed_size_no_rle)) if compressed_size_no_rle > 0 else 0.0

                if saved_images < args.save_images_limit:
                    base = out_dir / f'img{img_index:05d}_q{q}'
                    import tifffile
                    tifffile.imwrite(str(base) + '_recon.tiff', recon)
                    write_recon_vis(str(base), recon)
                    write_error_map(str(base), img, recon, bits_stored=bs)

                results.append({
                    'file': _display_file_id(fpath, args.data_dir),
                    'quality': q,
                    'bits_stored': int(bs),
                    'pixel_representation': int(pr),
                    'original_size': int(original_size),
                    'compressed_size': int(compressed_size),
                    'bpp': bpp,
                    'CR': cr,
                    'RMSE': rmse,
                    'PSNR': psnr,
                    'SSIM': ssim_val,
                    'Edge_SSIM': edge_ssim,
                    'compressed_size_no_rle': int(compressed_size_no_rle),
                    'bpp_no_rle': bpp_no_rle,
                    'CR_no_rle': cr_no_rle,
                    'rle_savings_frac': rle_savings,
                })
            if saved_images < args.save_images_limit:
                saved_images += 1
            img_index += 1
        except Exception:
            continue

    df = pd.DataFrame(results)
    csv_path = out_dir / 'results.csv'
    df.to_csv(csv_path, index=False)
    print(f'Wrote: {csv_path}')

    if not df.empty:
        summary = df.groupby('quality')[['bpp', 'CR', 'RMSE', 'PSNR', 'SSIM', 'Edge_SSIM', 'rle_savings_frac']].mean().reset_index()
        summary_path = out_dir / 'summary_by_quality.csv'
        summary.to_csv(summary_path, index=False)
        print(f'Wrote: {summary_path}')

        try:
            import matplotlib.pyplot as plt

            plt.figure()
            plt.plot(summary['bpp'], summary['PSNR'], marker='o')
            for _, row in summary.iterrows():
                plt.annotate(
                    f"q={int(row['quality'])}",
                    (float(row['bpp']), float(row['PSNR'])),
                    textcoords='offset points',
                    xytext=(0, 8),
                    ha='center',
                    va='bottom',
                    fontsize=9,
                )
            plt.xlabel('bpp')
            plt.ylabel('PSNR (dB)')
            plt.title('Rate-Distortion (avg by quality)')
            plt.grid(True, alpha=0.3)
            rd_path = out_dir / 'rd_plot_psnr.png'
            plt.savefig(rd_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f'Wrote: {rd_path}')

            plt.figure()
            plt.plot(summary['bpp'], summary['SSIM'], marker='o')
            for _, row in summary.iterrows():
                plt.annotate(
                    f"q={int(row['quality'])}",
                    (float(row['bpp']), float(row['SSIM'])),
                    textcoords='offset points',
                    xytext=(0, 8),
                    ha='center',
                    va='bottom',
                    fontsize=9,
                )
            plt.xlabel('bpp')
            plt.ylabel('SSIM')
            plt.title('Rate-Distortion (SSIM, avg by quality)')
            plt.grid(True, alpha=0.3)
            rd_path = out_dir / 'rd_plot_ssim.png'
            plt.savefig(rd_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f'Wrote: {rd_path}')

            plt.figure()
            plt.plot(summary['quality'], summary['rle_savings_frac'] * 100.0, marker='o')
            plt.xlabel('quality')
            plt.ylabel('RLE savings (%)')
            plt.title('RLE Ablation: size reduction vs. storing all coefficients')
            plt.grid(True, alpha=0.3)
            ab_path = out_dir / 'ablation_rle_savings.png'
            plt.savefig(ab_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f'Wrote: {ab_path}')
        except Exception:
            pass


if __name__ == '__main__':
    main()
