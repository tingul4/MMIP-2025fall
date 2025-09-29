./dip_tool resize data/F16.bmp 512 512 128 128 nearest
./dip_tool resize data/F16.bmp 512 512 128 128 bilinear
./dip_tool resize data/F16.bmp 512 512 32 32 nearest
./dip_tool resize data/F16.bmp 512 512 32 32 bilinear
./dip_tool resize data/F16.bmp 32 32 512 512 nearest
./dip_tool resize data/F16.bmp 32 32 512 512 bilinear
# ./dip_tool resize out/C/F16_resize_512x512_to_32x32_nearest.png 32 32 512 512 nearest
# ./dip_tool resize out/C/F16_resize_512x512_to_32x32_bilinear.png 32 32 512 512 bilinear
./dip_tool resize data/F16.bmp 512 512 1024 512 nearest
./dip_tool resize data/F16.bmp 512 512 1024 512 bilinear
./dip_tool resize data/F16.bmp 128 128 256 512 nearest
./dip_tool resize data/F16.bmp 128 128 256 512 bilinear
# ./dip_tool resize out/C/F16_resize_512x512_to_128x128_nearest.png 128 128 256 512 nearest
# ./dip_tool resize out/C/F16_resize_512x512_to_128x128_bilinear.png 128 128 256 512 bilinear