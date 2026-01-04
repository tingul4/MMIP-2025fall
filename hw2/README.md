# Medical Image Codec (Custom Lossy Compression)

**Course:** Multi-Modal Image Processing  
**Assignment:** Build a Lossy Medical Image Codec with a Custom Bitstream  
**Language:** Python 3.8+

## 1. Project Overview
This project implements a **lossy image compression system** specifically designed for high-bit-depth medical images (12-16 bit DICOM). It avoids using standard codecs (like JPEG/PNG) and implements the entire pipeline from scratch, including:
1.  **Transformation:** 8x8 Block DCT (Discrete Cosine Transform).
2.  **Quantization:** Scalar quantization with dynamic quality scaling (preserving 16-bit dynamic range).
3.  **Entropy Coding:** Run-Length Encoding (RLE) on ZigZag scanned coefficients.
4.  **Bitstream:** A custom binary file format with header and payload packing.

## 2. Environment Setup

**Requirements:**
- Python 3.8 or higher
- Virtual environment (conda or venv) recommended

```bash
# Create virtual environment (optional but recommended)
conda create -n medical_codec python=3.8
conda activate medical_codec

# Install dependencies
pip install -r requirements.txt
```

## 3. Quick Start: Test the Codec

Before running full experiments, test the codec with a single DICOM file:

```bash
# Encode a DICOM slice (quality: 30=low, 50=medium, 80=high)
./encode --input <path_to_single_dicom_file> --output test.medc --quality 50

# Decode the compressed file
./decode --input test.medc --output test_reconstructed.tiff
```

**Alternative:** Use Python directly:
```bash
python main.py encode --input <path_to_single_dicom_file> --output test.medc --quality 50
python main.py decode --input test.medc --output test_reconstructed.tiff
```

### Output Format Options:
- `.tif`/`.tiff`: Preserves signed/unsigned 16-bit values (recommended for medical images)
- `.png`: 16-bit output; signed int16 values stored with +32768 offset
- `.npy`: Exact NumPy array format

## 4. Datasets

This project uses two medical imaging datasets for evaluation:

### Dataset A: Medimodel Skull CT (303 slices)
- **Download:** https://medimodel.com/sample-dicom-files/human_skull_2_dicom_file/
- **Description:** High-resolution skull CT scan with 303 DICOM slices
- **Usage:** Extract the downloaded ZIP file to your preferred location (e.g., `<path_to_dataset_A>/`)

### Dataset C: TCIA RIDER Lung CT (1000 slices subset)
- **Download:** https://www.cancerimagingarchive.net/collection/rider-lung-ct/
- **Description:** Reference Image Database to Evaluate Therapy Response (RIDER) lung CT collection
- **Usage:** After downloading via NBIA Data Retriever, place the DICOM files in a folder (e.g., `<path_to_dataset_C>/`)
- **Note:** A metadata manifest is included in this repository for reference, but actual DICOM files must be downloaded separately

**Important:** The paths shown in examples below are placeholders. Replace `<path_to_dataset_A>` and `<path_to_dataset_C>` with your actual dataset locations when running experiments.

## 5. Reproducibility: Generate Quantitative Results

To reproduce the tables and figures in the report, run the following experiments:

### Dataset A (303 slices):
```bash
python run_experiments.py --data_dir <path_to_dataset_A> \
    --output_dir results/experiments_dataset_a --qualities 30 50 80 \
    --write_bitstreams --save_images_limit 5
```

### Dataset C (1000 slices):
```bash
python run_experiments.py --data_dir <path_to_dataset_C> \
    --output_dir results/experiments_dataset_c --qualities 30 50 80 \
    --limit 1000 --write_bitstreams --save_images_limit 5
```

**Replace the placeholders:**
- `<path_to_dataset_A>`: Path to your extracted Medimodel Skull CT folder
- `<path_to_dataset_C>`: Path to your TCIA RIDER Lung CT folder

### Expected Outputs:

After running experiments, the output directory will contain:

- **CSV files:** `results.csv` (per-image metrics) and `summary_by_quality.csv` (averaged metrics for Tables II-III)
- **Reconstructed images:** `*_recon.tiff` for the first 5 images per quality level (Figure 2)
- **Error maps:** `*_abs_error.tiff` (16-bit TIFF) and `*_abs_error_vis.png` (8-bit visualization for Figure 3)
- **Performance plots:** `ablation_rle_savings.png`, `rd_plot_psnr.png`, `rd_plot_ssim.png` (Figures 1 and 4)
- **Compressed files:** `*.medc` bitstreams (if `--write_bitstreams` flag is used)

### Generate Report Figures from Results:

If you want to regenerate publication-quality figures from existing CSV results:

```bash
python prepare_report_figures.py \
    --data_dir_a results/experiments_dataset_a \
    --data_dir_c results/experiments_dataset_c \
    --output_dir report_figures
```

This will create polished versions of all plots used in the paper.

## 6. Troubleshooting

**Common Issues:**

1. **"No module named 'pydicom'"**
   - Solution: Run `pip install -r requirements.txt`

2. **"Permission denied: ./encode"**
   - Solution: Make scripts executable: `chmod +x encode decode`
   - Alternative: Use `python main.py encode/decode` instead

3. **Experiments run slowly on large datasets**
   - Solution: Use `--limit N` to process only N images for testing
   - Example: `--limit 10` processes first 10 images only

4. **Out of memory during experiments**
   - Solution: Process images in smaller batches or reduce `--save_images_limit`

## 7. Bitstream Specification

Binary file format (big-endian):

**Header fields (28 bytes):**
- magic: 4 bytes (`MEDC`)
- version: 1 byte (current: 3)
- height: uint16
- width: uint16
- quality: uint8
- scale_factor: float32
- bits_stored: uint8 (1..16)
- pixel_representation: uint8 (0=unsigned, 1=signed; matches DICOM `PixelRepresentation`)
- ROI: rx, ry, rw, rh (each uint16) - Region of Interest coordinates

**Payload:**
- payload_len_bytes: uint32 (length of coefficient stream in bytes)
- payload: int32 array bytes (RLE-encoded DCT coefficients in zigzag order)