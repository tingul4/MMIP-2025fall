# src/bitstream.py (確保 Writer 與 Reader 都是 int32)
import struct
import numpy as np

class BitStreamWriter:
    def __init__(self, filename):
        self.file = open(filename, 'wb')
        
    def write_header(self, height, width, quality, scale_factor, *, bits_stored=16, pixel_representation=1, roi=None):
        rx, ry, rw, rh = roi if roi else (0, 0, 0, 0)
        # Magic(4s), Ver(B), H(H), W(H), Q(B), Scale(f), BitsStored(B), PixelRep(B), ROI(4H)
        # PixelRep: 0=unsigned, 1=signed (DICOM PixelRepresentation)
        if not (1 <= int(bits_stored) <= 16):
            raise ValueError(f"bits_stored must be 1..16, got {bits_stored}")
        if int(pixel_representation) not in (0, 1):
            raise ValueError(f"pixel_representation must be 0 or 1, got {pixel_representation}")
        header = struct.pack(
            '>4sBHHBfBBHHHH',
            b'MEDC',
            3,
            int(height),
            int(width),
            int(quality),
            float(scale_factor),
            int(bits_stored),
            int(pixel_representation),
            int(rx),
            int(ry),
            int(rw),
            int(rh),
        )
        self.file.write(header)

    def write_block_data(self, data_stream):
        # ⚠️ 關鍵：寫入時強制轉為 int32
        raw_data = np.array(data_stream, dtype=np.int32).tobytes()
        self.file.write(struct.pack('>I', len(raw_data)))
        self.file.write(raw_data)

    def close(self):
        self.file.close()

class BitStreamReader:
    def __init__(self, filename):
        self.file = open(filename, 'rb')
        
    def read_header(self):
        header_len = struct.calcsize('>4sBHHBfBBHHHH')
        data = self.file.read(header_len)
        if len(data) < header_len:
            raise ValueError("Invalid file header (too short)")
        magic, ver, h, w, q, scale, bits_stored, pixel_representation, rx, ry, rw, rh = struct.unpack(
            '>4sBHHBfBBHHHH', data
        )
        if magic != b'MEDC': raise ValueError("Invalid Magic Number")
        if ver != 3:
            raise ValueError(f"Unsupported bitstream version: {ver}")
        if bits_stored < 1 or bits_stored > 16:
            raise ValueError(f"Invalid bits_stored in header: {bits_stored}")
        if pixel_representation not in (0, 1):
            raise ValueError(f"Invalid pixel_representation in header: {pixel_representation}")
        return h, w, q, scale, int(bits_stored), int(pixel_representation), (rx, ry, rw, rh)

    def read_block_data(self):
        len_bytes = self.file.read(4)
        if not len_bytes:
            raise ValueError("Missing payload length (corrupt stream)")
        len_data = struct.unpack('>I', len_bytes)[0]
        raw_data = self.file.read(len_data)
        if len(raw_data) != len_data:
            raise ValueError("Truncated payload (corrupt stream)")
        if len_data % 4 != 0:
            raise ValueError("Invalid payload length (not int32-aligned)")
        
        # ⚠️ 關鍵：讀取時必須也是 int32，否則 40000 會被讀成兩個數字(其中一個是負的)
        return np.frombuffer(raw_data, dtype=np.int32)

    def close(self):
        self.file.close()