#ifndef IMAGE_H
#define IMAGE_H

typedef struct
{
    int w, h, c;         // width, height, channels (1=gray, 3=RGB)
    unsigned char *data; // size = w*h*c
} Image;

Image *read_image(const char *path); // jpg/png via stb
Image *read_raw(const char *path, int w, int h, int c);
void save_png(const char *path, const Image *img);

// point operations
Image *point_log(const Image *img);
Image *point_gamma(const Image *img, double gamma);
Image *point_negative(const Image *img);

// resizing
Image *resize_nearest(const Image *img, int out_w, int out_h);
Image *resize_bilinear(const Image *img, int out_w, int out_h);

// utils
Image *create_image(int w, int h, int c);
void free_image(Image *img);
const char *file_stem(const char *path);

#endif
