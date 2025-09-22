#ifndef IMAGE_H
#define IMAGE_H

typedef struct {
    int w, h, c;          // width, height, channels (1=gray, 3=RGB)
    unsigned char *data;  // size = w*h*c
} Image;

Image* read_image(const char *path);                 // jpg/png via stb
Image* read_raw_512(const char *path);               // 512x512, 1ch
void    save_png(const char *path, const Image *im);

Image* to_grayscale(const Image *im);
Image* to_grayscale_with_hint(const Image *im, int expect_w, int expect_h);
unsigned char rgb2gray_px(const unsigned char *rgb);

// point operations
Image* point_log(const Image *g1);
Image* point_gamma(const Image *g1, double gamma);
Image* point_negative(const Image *g1);

// resizing
Image* resize_nearest(const Image *g1, int out_w, int out_h);
Image* resize_bilinear(const Image *g1, int out_w, int out_h);

// utils
Image* create_image(int w, int h, int c);
void   free_image(Image *im);
const char* file_stem(const char *path);

#endif
