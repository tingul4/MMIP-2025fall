// Digital Image Processing Assignment 1
// Build: see Makefile
// Usage examples:
//   ./dip_tool read_raw path/to/img.raw
//   ./dip_tool read_jpg boat.jpg
//   ./dip_tool point_op baboon.jpg log
//   ./dip_tool point_op baboon.jpg gamma 2.2
//   ./dip_tool point_op baboon.jpg negative
//   ./dip_tool resize F16.jpg 512 512 128 128 nearest
//   ./dip_tool resize F16.jpg 512 512 32 32 bilinear
//   ./dip_tool resize F16.jpg 32 32 512 512 bilinear
// Output files are saved under ./out/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "image.h"

static void ensure_out_dir(void) {
#ifdef _WIN32
    system("if not exist out mkdir out");
#else
    system("mkdir -p out");
#endif
}

static void print_center_10x10(const Image *im, const char *tag) {
    int cx = im->w / 2, cy = im->h / 2;
    int x0 = cx - 5, y0 = cy - 5;
    printf("Center 10x10 (%s):\n", tag);
    for (int y = 0; y < 10; ++y) {
        for (int x = 0; x < 10; ++x) {
            int xi = x0 + x, yi = y0 + y;
            xi = xi < 0 ? 0 : (xi >= im->w ? im->w - 1 : xi);
            yi = yi < 0 ? 0 : (yi >= im->h ? im->h - 1 : yi);
            unsigned char v = im->c == 1
                              ? im->data[yi * im->w + xi]
                              : rgb2gray_px(&im->data[(yi * im->w + xi) * 3]);
            printf("%3d ", (int)v);
        }
        printf("\n");
    }
}

static void cmd_read_raw(const char *path) {
    ensure_out_dir();
    Image *im = read_raw_512(path); // 512x512, 1 channel
    if (!im) { fprintf(stderr, "Failed to read RAW\n"); return; }
    print_center_10x10(im, path);
    save_png("out/raw_view.png", im); // PNG for convenience
    free_image(im);
    printf("Saved out/raw_view.png\n");
}

static void cmd_read_jpg(const char *path) {
    ensure_out_dir();
    Image *im = read_image(path); // loads as 1 or 3 channels depending on file
    if (!im) { fprintf(stderr, "Failed to read image\n"); return; }
    print_center_10x10(im, path);
    save_png("out/jpg_view.png", im);
    // also save grayscale version to match assignment grayscale displays
    Image *gray = to_grayscale(im);
    save_png("out/jpg_gray.png", gray);
    free_image(gray);
    free_image(im);
    printf("Saved out/jpg_view.png and out/jpg_gray.png\n");
}

static void cmd_point_op(const char *path, const char *op, double param) {
    ensure_out_dir();
    Image *im = read_image(path);
    if (!im) { fprintf(stderr, "Cannot read %s\n", path); return; }
    Image *g = to_grayscale(im);

    Image *res = NULL;
    if (strcmp(op, "log") == 0) {
        res = point_log(g);
    } else if (strcmp(op, "gamma") == 0) {
        if (param <= 0) param = 1.0;
        res = point_gamma(g, param);
    } else if (strcmp(op, "negative") == 0) {
        res = point_negative(g);
    } else {
        fprintf(stderr, "Unknown op: %s\n", op);
    }
    if (res) {
        char outp[256];
        if (strcmp(op, "gamma") == 0)
            snprintf(outp, sizeof(outp), "out/%s_gamma_%.2f.png", file_stem(path), param);
        else
            snprintf(outp, sizeof(outp), "out/%s_%s.png", file_stem(path), op);
        save_png(outp, res);
        print_center_10x10(res, op);
        free_image(res);
        printf("Saved %s\n", outp);
    }
    free_image(g);
    free_image(im);
}

static void cmd_resize(const char *path,
                       int in_w, int in_h,
                       int out_w, int out_h,
                       const char *method) {
    ensure_out_dir();
    Image *im = read_image(path);
    if (!im) { fprintf(stderr, "Cannot read %s\n", path); return; }
    Image *g = to_grayscale_with_hint(im, in_w, in_h); // if file is RAW-like size hint

    Image *res = NULL;
    if (strcmp(method, "nearest") == 0) {
        res = resize_nearest(g, out_w, out_h);
    } else if (strcmp(method, "bilinear") == 0) {
        res = resize_bilinear(g, out_w, out_h);
    } else {
        fprintf(stderr, "Unknown method: %s\n", method);
    }
    if (res) {
        char outp[256];
        snprintf(outp, sizeof(outp), "out/resize_%dx%d_to_%dx%d_%s.png",
                 g->w, g->h, out_w, out_h, method);
        save_png(outp, res);
        print_center_10x10(res, "resized");
        free_image(res);
        printf("Saved %s\n", outp);
    }
    free_image(g);
    free_image(im);
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr,
            "Usage:\n"
            "  %s read_raw <path.raw>\n"
            "  %s read_jpg <path.jpg>\n"
            "  %s point_op <path.(jpg/png)> <log|gamma|negative> [gamma]\n"
            "  %s resize <path.(raw/jpg/png)> <in_w> <in_h> <out_w> <out_h> <nearest|bilinear>\n",
            argv[0], argv[0], argv[0], argv[0]);
        return 1;
    }
    if (strcmp(argv[1], "read_raw") == 0) {
        cmd_read_raw(argv[2]);
    } else if (strcmp(argv[1], "read_jpg") == 0) {
        cmd_read_jpg(argv[2]);
    } else if (strcmp(argv[1], "point_op") == 0) {
        double g = (argc >= 5) ? atof(argv[4]) : 1.0;
        cmd_point_op(argv[2], argv[3], g);
    } else if (strcmp(argv[1], "resize") == 0) {
        if (argc < 8) { fprintf(stderr, "resize args missing\n"); return 1; }
        int iw = atoi(argv[3]), ih = atoi(argv[4]);
        int ow = atoi(argv[5]), oh = atoi(argv[6]);
        cmd_resize(argv[2], iw, ih, ow, oh, argv[7]);
    } else {
        fprintf(stderr, "Unknown command.\n");
        return 1;
    }
    return 0;
}
