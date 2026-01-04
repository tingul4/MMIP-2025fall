import numpy as np
from skimage.metrics import structural_similarity as ssim

def calculate_metrics(original, decoded, encoded_size, *, bit_depth=16):
    """
    計算 CR (Compression Ratio), MSE, RMSE, PSNR
    PSNR uses MAX = 2^B - 1 (assignment requirement).
    """
    # Compression Ratio (原始大小 / 壓縮後大小)
    original_size = original.nbytes
    cr = original_size / encoded_size if encoded_size > 0 else 0

    # MSE (Mean Squared Error)
    original_f = original.astype(np.float64)
    decoded_f = decoded.astype(np.float64)
    mse = np.mean((original_f - decoded_f) ** 2)
    rmse = float(np.sqrt(mse))

    # PSNR (Peak Signal-to-Noise Ratio)
    if mse == 0:
        psnr = float('inf')
    else:
        bit_depth = int(bit_depth)
        if bit_depth < 1 or bit_depth > 16:
            bit_depth = 16
        max_pixel = float((1 << bit_depth) - 1)
        psnr = 20 * np.log10(max_pixel / rmse)

    return {
        "CR": cr,
        "MSE": mse,
        "RMSE": rmse,
        "PSNR": psnr
    }