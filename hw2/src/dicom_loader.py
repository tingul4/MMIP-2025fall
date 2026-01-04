import pydicom
import numpy as np
import os

class DicoLoader:
    def load_dicom(self, filepath):
        """
        讀取 DICOM 檔案並分離 Metadata 與 Pixel Data
        Return: (dataset object, numpy array of pixel data)
        """
        try:
            ds = pydicom.dcmread(filepath)
            # 確保數據為 numpy array，通常 CT 是 uint16 或 int16
            pixel_data = ds.pixel_array
            return ds, pixel_data
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return None, None

    def get_scan_files(self, directory):
        """遞迴找出目錄下所有 .dcm 檔案"""
        dcm_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".dcm"):
                    dcm_files.append(os.path.join(root, file))
        return dcm_files