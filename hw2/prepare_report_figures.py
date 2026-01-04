#!/usr/bin/env python3
"""
Generate figures for the IEEE report from experimental results.
This script reads CSV results from hw2/reports/experiments_dataset_a and
hw2/reports/experiments_dataset_c, then generates publication-quality figures.
"""

import argparse
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_experiment_results(dataset_dir):
    """Load results.csv from an experiment directory."""
    csv_path = Path(dataset_dir) / 'results.csv'
    if not csv_path.exists():
        raise FileNotFoundError(f"Results CSV not found: {csv_path}")
    return pd.read_csv(csv_path)

def plot_rd_curves(df, output_dir, dataset_name):
    """
    Generate rate-distortion plots for PSNR and SSIM.
    Assumes df contains columns: bpp, PSNR, SSIM, quality
    """
    summary = df.groupby('quality')[['bpp', 'CR', 'RMSE', 'PSNR', 'SSIM']].mean().reset_index()
    
    # PSNR vs bpp
    plt.figure(figsize=(6, 4))
    plt.plot(summary['bpp'], summary['PSNR'], marker='o', linewidth=2, markersize=8)
    for _, row in summary.iterrows():
        plt.annotate(
            f"q={int(row['quality'])}",
            (float(row['bpp']), float(row['PSNR'])),
            textcoords='offset points',
            xytext=(0, 8),
            ha='center',
            va='bottom',
            fontsize=10,
        )
    plt.xlabel('bpp', fontsize=11)
    plt.ylabel('PSNR (dB)', fontsize=11)
    plt.title(f'Rate-Distortion: {dataset_name}', fontsize=12)
    plt.grid(True, alpha=0.3)
    psnr_path = Path(output_dir) / f'rd_psnr_{dataset_name.lower().replace(" ", "_")}.png'
    plt.savefig(psnr_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {psnr_path}")
    
    # SSIM vs bpp
    plt.figure(figsize=(6, 4))
    plt.plot(summary['bpp'], summary['SSIM'], marker='o', linewidth=2, markersize=8)
    for _, row in summary.iterrows():
        plt.annotate(
            f"q={int(row['quality'])}",
            (float(row['bpp']), float(row['SSIM'])),
            textcoords='offset points',
            xytext=(0, 8),
            ha='center',
            va='bottom',
            fontsize=10,
        )
    plt.xlabel('bpp', fontsize=11)
    plt.ylabel('SSIM', fontsize=11)
    plt.title(f'Rate-Distortion (SSIM): {dataset_name}', fontsize=12)
    plt.grid(True, alpha=0.3)
    ssim_path = Path(output_dir) / f'rd_ssim_{dataset_name.lower().replace(" ", "_")}.png'
    plt.savefig(ssim_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {ssim_path}")

def plot_rle_ablation(df, output_dir, dataset_name):
    """
    Generate RLE ablation plot showing size reduction vs. raw coefficients.
    Assumes df contains column: rle_savings_frac
    """
    summary = df.groupby('quality')['rle_savings_frac'].mean().reset_index()
    
    plt.figure(figsize=(6, 4))
    plt.plot(summary['quality'], summary['rle_savings_frac'] * 100.0, marker='o', linewidth=2, markersize=8)
    plt.xlabel('Quality parameter', fontsize=11)
    plt.ylabel('RLE size reduction (%)', fontsize=11)
    plt.title(f'RLE Ablation: {dataset_name}', fontsize=12)
    plt.grid(True, alpha=0.3)
    ab_path = Path(output_dir) / f'ablation_rle_{dataset_name.lower().replace(" ", "_")}.png'
    plt.savefig(ab_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {ab_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Generate publication-quality figures for the IEEE report.'
    )
    parser.add_argument(
        '--data_dir_a',
        default='hw2/reports/experiments_dataset_a',
        help='Path to Dataset A results directory',
    )
    parser.add_argument(
        '--data_dir_c',
        default='hw2/reports/experiments_dataset_c',
        help='Path to Dataset C results directory',
    )
    parser.add_argument(
        '--output_dir',
        default='hw2/report_ieee/figures',
        help='Where to save generated figures',
    )
    args = parser.parse_args()
    
    out_path = Path(args.output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    print("Generating figures for Dataset A...")
    df_a = load_experiment_results(args.data_dir_a)
    plot_rd_curves(df_a, out_path, 'Dataset A')
    plot_rle_ablation(df_a, out_path, 'Dataset A')
    
    print("\nGenerating figures for Dataset C...")
    df_c = load_experiment_results(args.data_dir_c)
    plot_rd_curves(df_c, out_path, 'Dataset C')
    plot_rle_ablation(df_c, out_path, 'Dataset C')
    
    print(f"\nAll figures saved to: {out_path}")

if __name__ == '__main__':
    main()
