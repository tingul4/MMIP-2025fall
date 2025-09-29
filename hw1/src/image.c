#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#include "image.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

static char stem_buf[256];

const char *file_stem(const char *path)
{
    const char *slash = strrchr(path, '/');
#ifdef _WIN32
    const char *bslash = strrchr(path, '\\');
    if (!slash || (bslash && bslash > slash))
        slash = bslash;
#endif
    const char *name = slash ? slash + 1 : path;
    snprintf(stem_buf, sizeof(stem_buf), "%s", name);
    char *dot = strrchr(stem_buf, '.');
    if (dot)
        *dot = '\0';
    return stem_buf;
}

/**  分配image所需的記憶體空間 */
Image *create_image(int w, int h, int c)
{
    Image *img = (Image *)malloc(sizeof(Image));
    img->w = w;
    img->h = h;
    img->c = c;
    img->data = (unsigned char *)malloc((size_t)w * h * c);
    return img;
}

/** 釋放image的記憶體 */
void free_image(Image *img)
{
    if (!img)
        return;
    free(img->data);
    free(img);
}

Image *read_image(const char *path)
{
    int w, h, c;
    unsigned char *data = stbi_load(path, &w, &h, &c, 0);
    if (!data)
        return NULL;
    Image *img = (Image *)malloc(sizeof(Image));
    img->w = w;
    img->h = h;
    img->c = c;
    img->data = data;
    printf("Loaded %s: %dx%d, %d channels\n", path, w, h, c);
    return img;
}

Image *read_raw(const char *path, int w, int h, int c)
{
    FILE *fp = fopen(path, "rb");
    if (!fp)
        return NULL;
    Image *img = create_image(w, h, c);
    size_t need = (size_t)w * h * c;
    size_t got = fread(img->data, 1, need, fp);
    fclose(fp);
    if (got != need)
    {
        free_image(img);
        return NULL;
    }
    return img;
}

void save_png(const char *path, const Image *img)
{
    if (img->c == 1)
    {
        stbi_write_png(path, img->w, img->h, 1, img->data, img->w);
    }
    else
    {
        stbi_write_png(path, img->w, img->h, 3, img->data, img->w * 3);
    }
}

// ---------------- Point operations ----------------
/** 防止數值運算結果超出範圍0-255 */
static inline unsigned char clamp255(int v)
{
    if (v < 0)
        return 0;
    if (v > 255)
        return 255;
    return (unsigned char)v;
}
/** log transform */
Image *point_log(const Image *img)
{
    Image *out = create_image(img->w, img->h, img->c);
    double c = 255.0 / log(256.0);
    for (int i = 0; i < img->w * img->h * img->c; ++i)
    {
        double r = img->data[i];
        int s = (int)round(c * log(1.0 + r));
        out->data[i] = clamp255(s);
    }
    return out;
}

Image *point_gamma(const Image *img, double gamma)
{
    Image *out = create_image(img->w, img->h, img->c);
    double inv = 1.0 / 255.0;
    for (int i = 0; i < img->w * img->h * img->c; ++i)
    {
        double nr = img->data[i] * inv;
        int s = (int)round(255.0 * pow(nr, gamma));
        out->data[i] = clamp255(s);
    }
    return out;
}

Image *point_negative(const Image *img)
{
    Image *out = create_image(img->w, img->h, img->c);
    for (int i = 0; i < img->w * img->h * img->c; ++i)
        out->data[i] = (unsigned char)(255 - img->data[i]);
    return out;
}

// ---------------- Resizing ----------------
/** 防止resize時得到的數值超出圖片的邊界 */
static inline unsigned char get_pixel(const Image *img, int x, int y, int c)
{
    if (x < 0)
        x = 0;
    if (x >= img->w)
        x = img->w - 1;
    if (y < 0)
        y = 0;
    if (y >= img->h)
        y = img->h - 1;
    return img->data[(y * img->w + x) * img->c + c];
}

Image *resize_nearest(const Image *img, int out_w, int out_h)
{
    Image *out = create_image(out_w, out_h, img->c);
    double sx = (double)img->w / out_w;
    double sy = (double)img->h / out_h;
    for (int y = 0; y < out_h; ++y)
    {
        int syi = (int)floor(y * sy + 0.5);
        if (syi < 0)
            syi = 0;
        if (syi >= img->h)
            syi = img->h - 1;
        for (int x = 0; x < out_w; ++x)
        {
            int sxi = (int)floor(x * sx + 0.5);
            if (sxi < 0)
                sxi = 0;
            if (sxi >= img->w)
                sxi = img->w - 1;
            memcpy(&out->data[(y * out_w + x) * img->c], &img->data[(syi * img->w + sxi) * img->c], img->c);
        }
    }
    return out;
}

Image *resize_bilinear(const Image *img, int out_w, int out_h)
{
    Image *out = create_image(out_w, out_h, img->c);
    double scale_x = (double)img->w / out_w;
    double scale_y = (double)img->h / out_h;
    for (int y = 0; y < out_h; ++y)
    {
        double gy = (y + 0.5) * scale_y - 0.5;
        int y0 = (int)floor(gy);
        int y1 = y0 + 1;
        double wy = gy - y0;
        for (int x = 0; x < out_w; ++x)
        {
            double gx = (x + 0.5) * scale_x - 0.5;
            int x0 = (int)floor(gx);
            int x1 = x0 + 1;
            double wx = gx - x0;

            for (int c = 0; c < img->c; ++c)
            {
                double I00 = get_pixel(img, x0, y0, c);
                double I10 = get_pixel(img, x1, y0, c);
                double I01 = get_pixel(img, x0, y1, c);
                double I11 = get_pixel(img, x1, y1, c);

                double top = (1 - wx) * I00 + wx * I10;
                double bot = (1 - wx) * I01 + wx * I11;
                int s = (int)round((1 - wy) * top + wy * bot);
                if (s < 0)
                    s = 0;
                if (s > 255)
                    s = 255;
                out->data[(y * out_w + x) * img->c + c] = (unsigned char)s;
            }
        }
    }
    return out;
}
