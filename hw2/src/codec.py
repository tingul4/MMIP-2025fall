# src/codec.py
import numpy as np


def _dct_matrix(n: int = 8) -> np.ndarray:
    # Orthonormal DCT-II transform matrix.
    k = np.arange(n, dtype=np.float32)[:, None]
    x = np.arange(n, dtype=np.float32)[None, :]
    mat = np.cos((np.pi / (2.0 * n)) * (2.0 * x + 1.0) * k)
    mat[0, :] *= np.sqrt(1.0 / n)
    mat[1:, :] *= np.sqrt(2.0 / n)
    return mat


_C8 = _dct_matrix(8)

# 標準 JPEG Luminance Table
Q_TABLE = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99]
], dtype=np.float32)

ZIGZAG_ORDER = np.array([
    0, 1, 8, 16, 9, 2, 3, 10,
    17, 24, 32, 25, 18, 11, 4, 5,
    12, 19, 26, 33, 40, 48, 41, 34,
    27, 20, 13, 6, 7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36, 29,
    22, 15, 23, 30, 37, 44, 51, 58,
    59, 52, 45, 38, 31, 39, 46, 53,
    60, 61, 54, 47, 55, 62, 63
])

def dct2(block):
    # 2D orthonormal DCT-II
    return _C8 @ block @ _C8.T

def idct2(block):
    # Inverse of orthonormal DCT-II is its transpose
    return _C8.T @ block @ _C8

def run_length_encode(arr):
    encoded = []
    zeros = 0
    for val in arr:
        if val == 0:
            zeros += 1
        else:
            if zeros > 0:
                encoded.extend([0, zeros])
                zeros = 0
            encoded.append(val)
    if zeros > 0:
        encoded.extend([0, zeros])
    return encoded

def run_length_decode(encoded):
    decoded = []
    i = 0
    while i < len(encoded):
        val = encoded[i]
        if val == 0:
            count = encoded[i+1]
            decoded.extend([0] * count)
            i += 2
        else:
            decoded.append(val)
            i += 1
    # ⚠️ 關鍵：解碼出來的串列必須轉為 int32
    return np.array(decoded, dtype=np.int32)

class MedicalCodec:
    def __init__(self, quality=50):
        if quality <= 0: quality = 1
        if quality > 100: quality = 100
        
        if quality < 50:
            self.scale = 5000 / quality
        else:
            self.scale = 200 - 2 * quality
            
        # 參數調校：使用 3.0 平衡方塊感與壓縮率
        global_multiplier = 3.0 
        base_scale = (self.scale / 50.0) * global_multiplier
        
        self.q_matrix_roi = Q_TABLE * (base_scale * 0.8) 
        self.q_matrix_bg = Q_TABLE * (base_scale * 1.2)

    def _finalize_output(self, img_recon, *, H, W, bits_stored=16, pixel_representation=1):
        out = img_recon[:H, :W]
        bits_stored = int(bits_stored)
        pixel_representation = int(pixel_representation)

        if pixel_representation == 0:
            max_val = (1 << bits_stored) - 1
            out = np.clip(np.round(out), 0, max_val).astype(np.uint16)
        else:
            min_val = -(1 << (bits_stored - 1))
            max_val = (1 << (bits_stored - 1)) - 1
            out = np.clip(np.round(out), min_val, max_val).astype(np.int16)
        return out

    def is_in_roi(self, r, c, roi):
        rx, ry, rw, rh = roi
        if rw == 0 or rh == 0: return False
        center_y, center_x = r + 4, c + 4
        return (rx <= center_x < rx + rw) and (ry <= center_y < ry + rh)

    def encode(self, image, roi=None):
        H, W = image.shape
        pad_h = (8 - H % 8) % 8
        pad_w = (8 - W % 8) % 8
        img_padded = np.pad(image, ((0, pad_h), (0, pad_w)), 'edge')
        stream = []
        if roi is None: roi = (0,0,0,0)
        
        for r in range(0, H + pad_h, 8):
            for c in range(0, W + pad_w, 8):
                q_mat = self.q_matrix_roi if self.is_in_roi(r, c, roi) else self.q_matrix_bg
                block = img_padded[r:r+8, c:c+8].astype(np.float32)
                dct_block = dct2(block)
                
                # ⚠️ 關鍵：使用 int32 範圍的 Clip，防止編碼時就變黑
                q_raw = np.round(dct_block / q_mat)
                q_block = np.clip(q_raw, -2147483647, 2147483647).astype(np.int32)
                
                stream.extend(q_block.ravel()[ZIGZAG_ORDER])
        
        return run_length_encode(stream), H, W

    def decode(self, stream, H, W, scale_factor_override=None, roi=None, *, bits_stored=16, pixel_representation=1):
        if scale_factor_override:
            # 還原 Q Tables
            base_scale = (scale_factor_override / 50.0) * 3.0 # 對應 global_multiplier
            self.q_matrix_roi = Q_TABLE * (base_scale * 0.8)
            self.q_matrix_bg = Q_TABLE * (base_scale * 1.2)
            
        flat_data = run_length_decode(stream)
        pad_h = (8 - H % 8) % 8
        pad_w = (8 - W % 8) % 8
        full_h, full_w = H + pad_h, W + pad_w
        
        img_recon = np.zeros((full_h, full_w), dtype=np.float32)
        if roi is None: roi = (0,0,0,0)
        
        idx = 0
        for r in range(0, full_h, 8):
            for c in range(0, full_w, 8):
                q_mat = self.q_matrix_roi if self.is_in_roi(r, c, roi) else self.q_matrix_bg

                # ⚠️ 關鍵：暫存 block 必須是 int32，否則資料放進去瞬間會溢位變負數
                q_block = np.zeros(64, dtype=np.int32)
                q_block[ZIGZAG_ORDER] = flat_data[idx:idx+64]
                idx += 64

                dct_block = q_block.reshape((8, 8)) * q_mat
                img_recon[r:r+8, c:c+8] = idct2(dct_block)

        return self._finalize_output(img_recon, H=H, W=W, bits_stored=bits_stored, pixel_representation=pixel_representation)