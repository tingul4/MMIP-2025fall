import argparse
import time
import os
import sys
import pydicom
import numpy as np
from src.codec import MedicalCodec
from src.bitstream import BitStreamWriter, BitStreamReader

def _extract_bit_depth_info(ds, img):
    bits_stored = int(ds.get('BitsStored', 16))
    pixel_representation = int(ds.get('PixelRepresentation', 1))
    if bits_stored < 1 or bits_stored > 16:
        bits_stored = 16
    if pixel_representation not in (0, 1):
        # default: signed for CT-like
        pixel_representation = 1
    # Fallback if metadata missing: infer from dtype
    if ds.get('BitsStored', None) is None:
        bits_stored = 16 if img.dtype in (np.uint16, np.int16) else 8
    if ds.get('PixelRepresentation', None) is None:
        pixel_representation = 0 if img.dtype == np.uint16 else 1
    return bits_stored, pixel_representation

def _write_image_16bit(path, img):
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.tif', '.tiff'):
        import tifffile
        tifffile.imwrite(path, img)
        return
    if ext == '.png':
        import imageio.v3 as iio
        if img.dtype == np.int16:
            # PNG doesn't support signed 16-bit; store as uint16 with offset.
            img_u16 = (img.astype(np.int32) + 32768).clip(0, 65535).astype(np.uint16)
            iio.imwrite(path, img_u16)
        else:
            iio.imwrite(path, img.astype(np.uint16))
        return
    raise ValueError(f"Unsupported output format: {ext}. Use .npy/.png/.tif/.tiff")

def load_dicom_image(path):
    ds = pydicom.dcmread(path, force=True)
    return ds, ds.pixel_array

def encode_mode(args):
    ds, img = load_dicom_image(args.input)
    bits_stored, pixel_representation = _extract_bit_depth_info(ds, img)
    print(f"Encoding {args.input} ({img.shape}), bits_stored={bits_stored}, pixel_rep={pixel_representation}...")
    
    # 解析 ROI
    roi_tuple = None
    if args.roi:
        try:
            # format: "x,y,w,h" e.g., "100,100,200,200"
            roi_tuple = tuple(map(int, args.roi.split(',')))
            print(f"ROI Enabled: {roi_tuple}")
        except:
            print("Invalid ROI format. Using full image.")

    start = time.time()
    codec = MedicalCodec(quality=args.quality)
    compressed_data, h, w = codec.encode(img, roi=roi_tuple)
    
    writer = BitStreamWriter(args.output)
    writer.write_header(
        h,
        w,
        args.quality,
        codec.scale,
        bits_stored=bits_stored,
        pixel_representation=pixel_representation,
        roi=roi_tuple,
    )
    writer.write_block_data(compressed_data)
    writer.close()
    
    print(f"Done. Size: {os.path.getsize(args.output)} bytes. Time: {time.time()-start:.4f}s")

def decode_mode(args):
    reader = BitStreamReader(args.input)
    h, w, q, scale, bits_stored, pixel_representation, roi = reader.read_header()
    raw_stream = reader.read_block_data()
    reader.close()
    
    print(f"Decoding ({h}x{w}), Q={q}, bits_stored={bits_stored}, pixel_rep={pixel_representation}, ROI={roi}...")
    codec = MedicalCodec(quality=q)
    
    start = time.time()
    recon_img = codec.decode(
        raw_stream,
        h,
        w,
        scale_factor_override=scale,
        roi=roi,
        bits_stored=bits_stored,
        pixel_representation=pixel_representation,
    )
    
    if args.output.endswith('.npy'):
        np.save(args.output, recon_img)
    else:
        _write_image_16bit(args.output, recon_img)
    
    print(f"Done. Time: {time.time()-start:.4f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Encode
    enc = subparsers.add_parser('encode')
    enc.add_argument('--input', required=True)
    enc.add_argument('--output', required=True)
    enc.add_argument('--quality', type=int, default=50)
    enc.add_argument('--roi', type=str, help="ROI x,y,w,h (e.g. 150,150,200,200)")
    
    # Decode
    dec = subparsers.add_parser('decode')
    dec.add_argument('--input', required=True)
    dec.add_argument('--output', required=True)
    
    args = parser.parse_args()
    try:
        if args.command == 'encode':
            encode_mode(args)
        elif args.command == 'decode':
            decode_mode(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)