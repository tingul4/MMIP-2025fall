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

const char* file_stem(const char *path) {
    const char *slash = strrchr(path, '/');
#ifdef _WIN32
    const char *bslash = strrchr(path, '\\');
    if (!slash || (bslash && bslash > slash)) slash = bslash;
#endif
    const char *name = slash ? slash + 1 : path;
    snprintf(stem_buf, sizeof(stem_buf), "%s", name);
    char *dot = strrchr(stem_buf, '.');
    if (dot) *dot = '\0';
    return stem_buf;
}

/**  分配image所需的記憶體空間 */
Image* create_image(int w, int h, int c) {
    Image *im = (Image*)malloc(sizeof(Image));
    im->w = w; im->h = h; im->c = c;
    im->data = (unsigned char*)malloc((size_t)w*h*c);
    return im;
}

/** 釋放image的記憶體 */
void free_image(Image *im) {
    if (!im) return;
    free(im->data);
    free(im);
}

unsigned char rgb2gray_px(const unsigned char *rgb) {
    // ITU-R BT.601 luma approximation
    double y = 0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2];
    if (y < 0) y = 0;
    if (y > 255) y = 255;
    return (unsigned char)(y + 0.5);
}

Image* to_grayscale(const Image *im) {
    if (im->c == 1) {
        Image *cp = create_image(im->w, im->h, 1);
        memcpy(cp->data, im->data, (size_t)im->w*im->h);
        return cp;
    }
    Image *g = create_image(im->w, im->h, 1);
    for (int i = 0; i < im->w*im->h; ++i)
        g->data[i] = rgb2gray_px(&im->data[i*3]);
    return g;
}

Image* to_grayscale_with_hint(const Image *im, int expect_w, int expect_h) {
    Image *g = to_grayscale(im);
    // 如果原圖大小與期望不同，僅更新 metadata 讓後續訊息更清楚（資料仍相同）
    // 真正 RAW 來源時建議直接用 read_raw_512 讀取
    (void)expect_w; (void)expect_h;
    return g;
}

Image* read_image(const char *path) {
    int w,h,c;
    unsigned char *data = stbi_load(path, &w, &h, &c, 0);
    if (!data) return NULL;
    Image *im = (Image*)malloc(sizeof(Image));
    im->w = w; im->h = h; im->c = c;
    im->data = data;
    return im;
}

Image* read_raw_512(const char *path) {
    FILE *fp = fopen(path, "rb");
    if (!fp) return NULL;
    int w = 512, h = 512, c = 1;
    Image *im = create_image(w,h,c);
    size_t need = (size_t)w*h*c;
    size_t got = fread(im->data, 1, need, fp);
    fclose(fp);
    if (got != need) { free_image(im); return NULL; }
    return im;
}

void save_png(const char *path, const Image *im) {
    if (im->c == 1) {
        stbi_write_png(path, im->w, im->h, 1, im->data, im->w);
    } else {
        stbi_write_png(path, im->w, im->h, 3, im->data, im->w*3);
    }
}

// ---------------- Point operations ----------------
static inline unsigned char clamp255(int v){
    if (v < 0) return 0;
    if (v > 255) return 255;
    return (unsigned char)v;
}

Image* point_log(const Image *g1) {
    Image *out = create_image(g1->w, g1->h, 1);
    double c = 255.0 / log(256.0);
    for (int i=0;i<g1->w*g1->h;++i){
        double r = g1->data[i];
        int s = (int)round(c * log(1.0 + r));
        out->data[i] = clamp255(s);
    }
    return out;
}

Image* point_gamma(const Image *g1, double gamma) {
    Image *out = create_image(g1->w, g1->h, 1);
    double inv = 1.0 / 255.0;
    for (int i=0;i<g1->w*g1->h;++i){
        double nr = g1->data[i] * inv;
        int s = (int)round(255.0 * pow(nr, gamma));
        out->data[i] = clamp255(s);
    }
    return out;
}

Image* point_negative(const Image *g1) {
    Image *out = create_image(g1->w, g1->h, 1);
    for (int i=0;i<g1->w*g1->h;++i)
        out->data[i] = (unsigned char)(255 - g1->data[i]);
    return out;
}

// ---------------- Resizing ----------------
Image* resize_nearest(const Image *g1, int out_w, int out_h) {
    Image *out = create_image(out_w, out_h, 1);
    double sx = (double)g1->w / out_w;
    double sy = (double)g1->h / out_h;
    for (int y=0;y<out_h;++y){
        int syi = (int)floor(y*sy + 0.5);
        if (syi < 0) syi = 0;
        if (syi >= g1->h) syi = g1->h-1;
        for (int x=0;x<out_w;++x){
            int sxi = (int)floor(x*sx + 0.5);
            if (sxi < 0) sxi = 0;
            if (sxi >= g1->w) sxi = g1->w-1;
            out->data[y*out_w + x] = g1->data[syi*g1->w + sxi];
        }
    }
    return out;
}

static inline unsigned char at_clamp(const Image *g, int x, int y){
    if (x < 0) x = 0;
    if (x >= g->w) x = g->w-1;
    if (y < 0) y = 0;
    if (y >= g->h) y = g->h-1;
    return g->data[y*g->w + x];
}

Image* resize_bilinear(const Image *g1, int out_w, int out_h) {
    Image *out = create_image(out_w, out_h, 1);
    double scale_x = (double)g1->w / out_w;
    double scale_y = (double)g1->h / out_h;
    for (int y=0;y<out_h;++y){
        double gy = (y + 0.5)*scale_y - 0.5;
        int y0 = (int)floor(gy);
        int y1 = y0 + 1;
        double wy = gy - y0;
        for (int x=0;x<out_w;++x){
            double gx = (x + 0.5)*scale_x - 0.5;
            int x0 = (int)floor(gx);
            int x1 = x0 + 1;
            double wx = gx - x0;

            double I00 = at_clamp(g1, x0, y0);
            double I10 = at_clamp(g1, x1, y0);
            double I01 = at_clamp(g1, x0, y1);
            double I11 = at_clamp(g1, x1, y1);

            double top = (1-wx)*I00 + wx*I10;
            double bot = (1-wx)*I01 + wx*I11;
            int s = (int)round((1-wy)*top + wy*bot);
            if (s < 0) s = 0;
            if (s > 255) s = 255;
            out->data[y*out_w + x] = (unsigned char)s;
        }
    }
    return out;
}
