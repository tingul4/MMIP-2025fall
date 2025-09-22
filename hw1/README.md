# HW1

### 專案說明
本專案以標準 C 實作數位影像處理作業：影像讀取與顯示、中心 10×10 像素列印、點運算（log、gamma、negative），以及最近鄰與雙線性插值之下採樣與上採樣；支援 512×512 RAW 灰階與常見 JPEG/PNG 影像。[^10]

### 專案結構

```
├── data
│   ├── baboon.bmp
│   ├── boat.bmp
│   ├── F16.bmp
│   ├── goldhill.raw
│   ├── lena.raw
│   └── peppers.raw
├── dip_tool
├── Makefile
├── out
├── README.md
├── report
└── src
    ├── image.c
    ├── image.h
    ├── main.c
    ├── stb_image.h
    └── stb_image_write.h
```

### 建置

在專案根目錄執行下列指令產生可執行檔 dip_tool

```
make
```

刪除建置後的檔案

```
make clean
```


### 使用方式

**四個子命令，所有輸出會寫入 out/ 目錄並在終端印出中心 10×10 像素表格**

> 讀取 RAW（512×512、8-bit、row-major）

```
./dip_tool read_raw data/peppers.raw
```

> 讀取 JPEG/PNG 並顯示與灰階化輸出

```
./dip_tool read_jpg data/boat.bmp
```

> 點運算：log、gamma、negative（gamma 需額外參數）

```
./dip_tool point_op data/baboon.bmp log
./dip_tool point_op data/baboon.bmp gamma 2.2
./dip_tool point_op data/baboon.bmp negative
```

> 重採樣：Bilinear interpolation或Nearest neighbor interpolation，支援非等比例尺寸

```
./dip_tool resize data/F16.bmp 512 512 128 128 nearest
./dip_tool resize data/F16.bmp 512 512 32 32 bilinear
./dip_tool resize data/F16.bmp 32 32 512 512 bilinear
./dip_tool resize data/F16.bmp 512 512 1024 512 bilinear
./dip_tool resize data/F16.bmp 128 128 256 512 bilinear
```


### 功能說明

> 影像讀取

JPEG/PNG 以單檔函式庫載入，RAW 以 fread 直接讀入 512×512 灰階，像素順序為 row-major，所有讀入皆可輸出 PNG 以便檢視。

> 中心 10×10 列印

以影像中心為基準取 10×10 區塊，邊界 clamp，RGB 會先轉灰階後列印，數值以 0–255 顯示。

> 點運算

- log 轉換：s = c·log(1+r)，c = 255/log(256)，提升暗部對比。
- gamma：s = 255·(r/255)^γ；γ>1 壓抑亮部，γ<1 提升暗部。
- negative：s = 255 − r。
 
> 重採樣

- 最近鄰：對應座標取最接近整數像素，速度快、鋸齒明顯。
- 雙線性：以四鄰點做二次線性插值，邊界 clamp，畫質較平滑。

### Reference
- [stb](https://github.com/nothings/stb)
