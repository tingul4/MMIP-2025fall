# Multi-Modal Image Processing  
## Homework: Build a Lossy Medical Image Codec with a Custom Bitstream

### Release information
- **Release date:** 2025/12/15  
- **Due date:** 2026/01/06  
- **Team size:** 1–2 students (recommended: 2)  
- **Submission:** One `.zip` file on the course LMS  

---

## Learning objectives
- Understand how to turn lecture concepts (transform coding, quantization, entropy coding) into a working codec.  
- Analyze how medical-imaging constraints (bit-depth, noise, diagnostically relevant structures) influence compression design.  
- Design a decodable bitstream format without any side files.  
- Evaluate rate–distortion trade-offs and justify design choices through experiments.

---

## 1. Problem statement
You will build a **medical image compression system** with two command-line tools:

- `encode`: Reads an input image (or a 3D stack/volume), produces a compressed file in your format.  
- `decode`: Reads your compressed file, reconstructs the image (or stack/volume).  

Your codec must be **lossy** (i.e., reconstructed pixels may differ), but designed to **preserve diagnostically important content** at a chosen bitrate.

---

## 2. Minimum technical requirements

### 2.1 Input and output
- Support at least one medical modality with **>8-bit grayscale** (CT or MR recommended).  
- Handle **12–16-bit pixel precision** end-to-end (no silent 8-bit casting).  
- The decoder must **reproduce image dimensions and bit depth** from the bitstream header.

### 2.2 Codec pipeline
Your encoder must have at least these conceptual stages (implementation is up to you):

1. **Signal decorrelation**  
   Examples: block DCT, wavelets, prediction/DPCM, slice-to-slice prediction.  
2. **Quantization**  
   Apply coefficient/residual quantization with a user-controllable quality parameter.  
3. **Entropy coding**  
   Examples: Huffman, arithmetic, run-length + Huffman.  
4. **Bitstream packing**  
   Use a well-defined binary syntax (document format in your report).

### 2.3 Bitstream requirements
- Must be a **binary bitstream** (not JSON).  
- Include:
  - Magic number and version (for sanity-checks).  
  - All parameters required for decoding (e.g., block size, quantization step, Huffman tables if custom).  
- Decoder must **reject malformed streams** with an error message and non-zero exit code.

### 2.4 Command-line interface (CLI)
Your submission must include commands that reproduce results exactly:

```bash
encode --input <path> --output <path> --quality <q>
decode --input <path> --output <path>
```

---

## 3. Data for testing

Evaluate your codec using **real medical images** from approved public datasets:

### Dataset A — Medimodel sample DICOM files  
- **Source:** [Medimodel – Sample DICOM files](https://medimodel.com/sample-dicom-files/)  
- **Recommended case:** `Human_Skull_2 (CT)`  
- **Reason:** Small, anonymized dataset suitable for validating 16-bit pipeline and bitstream correctness.  
- **Usage:** Provided for education and research.

### Dataset B — OsiriX DICOM Image Library  
- **Source:** [OsiriX – DICOM Image Library](https://www.osirix-viewer.com/resources/dicom-image-library/)  
- **Select one CT or MR dataset.**  
- **Reason:** Contains many modalities and slice stacks, ideal for robustness testing.  
- **Note:** Datasets may use JPEG2000 transfer syntax — ensure your reader can decode or convert them to raw arrays beforehand.

### Dataset C — (Optional) The Cancer Imaging Archive (TCIA)  
- **Source:** [TCIA portal: Access the Data](https://www.cancerimagingarchive.net/access-data/)  
- **Example collection:** [Healthy Total Body CTs](https://www.cancerimagingarchive.net/collection/healthy-total-body-cts/)  
- **Reason:** Realistic large-scale clinical CT datasets, useful for scalability demonstrations.

---

## 4. Evaluation protocol

You must report results at **three operating points** (three quality/bitrate settings), including both rate and distortion metrics.

### 4.1 Rate metrics
- Compressed size (bytes).  
- Bits-per-pixel (bpp) for 2D, or bits-per-voxel for 3D images.  
- Compression ratio compared to uncompressed.  

### 4.2 Distortion metrics
- RMSE (root mean squared error).  
- PSNR using \( \text{MAX} = 2^B - 1 \) (where \( B \) = bit depth).  
- Recommended: SSIM or task-driven metrics (e.g., segmentation or edge preservation in ROI).  

Include at least one **qualitative figure**: reconstructed image + absolute error map (scaled for visibility).

---

## 5. Constraints and allowed tools

This is an **implementation-focused** course. Avoid using high-level codec functions.

Allowed:
- Libraries for file I/O (DICOM/PNG/TIFF) and basic linear algebra/array operations.

Not allowed:
- Any existing codec implementation (JPEG, JPEG2000, HEVC, AVIF, etc.).  
- One-line transform or entropy coding library calls (must implement your own).  
- Functions that replace the design objective.  

If any third-party code is used, you must **cite it** and **justify why it doesn’t replace the project’s goals**.

---

## 6. Deliverables

| Item | Expected content |
|------|------------------|
| **Code** | Source files, build scripts, and run instructions (must run on a clean environment). |
| **Executables** | `encode` and `decode` command-line tools. |
| **Bitstream spec** | Section in report describing headers, block syntax, and coded payload. |
| **Report** | 6–10 page PDF (design, experiments, results, ablations, limitations). |
| **Results** | Folder with reconstructed images and a CSV/JSON of metrics. |

---

## 7. Recommended project plan

1. **Week 1:** Choose dataset + define file format + implement I/O + build baseline (e.g., block transform + scalar quantizer, no entropy coding).  
2. **Week 2:** Implement entropy coding + robust decoder + parameter tuning; collect rate–distortion results.  
3. **Week 3:** Add improvements (ROI, adaptive quantization, 3D extension), finalize report and figures.

---

## 8. Extra credit options

- ROI-aware coding: Detect/annotate ROI and allocate more bits there.  
- Progressive decoding: Support coarse-to-fine bitstream refinement.  
- 3D extension: Exploit inter-slice redundancy via prediction or 3D transform.  
- Error resilience: Add resync markers or partial decode capability.  
- Task-based evaluation: Demonstrate downstream task robustness (e.g., segmentation or edge detection).

---

## 9. Report checklist

- One-page overview: what you built and why.  
- Bitstream specification: header + field descriptions + decoding sequence.  
- Rate–distortion table (three operating points) + at least one RD plot.  
- Qualitative results: reconstructed image and error maps.  
- Ablation study: e.g., with/without prediction, or different quantizers.  
- Limitations and future work.

---

## Appendix A: Example bitstream structure (optional)
You can design your own format. A suggested starting structure:

```
File header:
    magic (4B)
    version (1B)
    width (2B), height (2B)
    bit depth (1B)
    flags
Coding parameters:
    block size
    transform type ID
    quantization step
    optional tables
Payload:
    per-block or per-slice entropy-coded data
Footer (optional):
    checksum for corruption detection
```

---

## Appendix B: References and data sources

- **Medimodel.** Sample DICOM files.  
  [https://medimodel.com/sample-dicom-files/](https://medimodel.com/sample-dicom-files/) *(accessed 2025-12-12)*  
- **OsiriX.** DICOM Image Library.  
  [https://www.osirix-viewer.com/resources/dicom-image-library/](https://www.osirix-viewer.com/resources/dicom-image-library/) *(accessed 2025-12-12)*  
- **The Cancer Imaging Archive (TCIA).** Access the Data.  
  [https://www.cancerimagingarchive.net/access-data/](https://www.cancerimagingarchive.net/access-data/) *(accessed 2025-12-12)*  
- **TCIA.** Data Usage Policies and Restrictions.  
  [https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/](https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/) *(accessed 2025-12-12)*  
- **TCIA.** Healthy Total Body CTs collection.  
  [https://www.cancerimagingarchive.net/collection/healthy-total-body-cts/](https://www.cancerimagingarchive.net/collection/healthy-total-body-cts/) *(accessed 2025-12-12)*  
