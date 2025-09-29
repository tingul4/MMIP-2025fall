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

static void ensure_out_dir(void)
{
#ifdef _WIN32
    system("if not exist out mkdir out");
    system("if not exist out\\A mkdir out\\A");
    system("if not exist out\\B mkdir out\\B");
    system("if not exist out\\C mkdir out\\C");
#else
    if (system("mkdir -p out/A out/B out/C") != 0)
    {
        fprintf(stderr, "warning: failed to create out directory\n");
    }
#endif
}

static void save_center_10x10_into_png(const char *outp, const Image *img)
{
    int cx = img->w / 2, cy = img->h / 2;
    int x0 = cx - 5, y0 = cy - 5;
    printf("Center 10x10:\n");
    Image small;
    small.w = 10;
    small.h = 10;
    small.c = img->c;
    small.data = (unsigned char *)malloc(10 * 10 * img->c);
    for (int y = 0; y < 10; ++y)
    {
        for (int x = 0; x < 10; ++x)
        {
            int xi = x0 + x, yi = y0 + y;
            xi = xi < 0 ? 0 : (xi >= img->w ? img->w - 1 : xi);
            yi = yi < 0 ? 0 : (yi >= img->h ? img->h - 1 : yi);
            size_t src_idx = (size_t)yi * img->w + xi;
            size_t dst_idx = (size_t)y * small.w + x;
            memcpy(&small.data[dst_idx * img->c], &img->data[src_idx * img->c], img->c);
            printf("%3d ", (int)img->data[src_idx * img->c]);
        }
        printf("\n");
    }
    save_png(outp, &small);
    free(small.data);
}

static void cmd_read_image(const char *path)
{
    ensure_out_dir();
    Image *img = read_image(path);
    if (!img)
        img = read_raw(path, 512, 512, 1);
    if (!img)
    {
        fprintf(stderr, "Failed to read RAW\n");
        return;
    }

    char outp[256];
    snprintf(outp, sizeof(outp), "out/A/%s.png", file_stem(path));
    save_png(outp, img);
    printf("Saved image %s\n", outp);

    char outp_center[256];
    snprintf(outp_center, sizeof(outp_center), "out/A/%s_center.png", file_stem(path));
    save_center_10x10_into_png(outp_center, img);
    printf("Saved center %s\n", outp);
    free_image(img);
}

static void cmd_point_op(const char *path, const char *op, double param)
{
    ensure_out_dir();
    Image *img = read_image(path);
    if (!img)
        img = read_raw(path, 512, 512, 1);
    if (!img)
    {
        fprintf(stderr, "Cannot read %s\n", path);
        return;
    }

    Image *res = NULL;
    if (strcmp(op, "log") == 0)
    {
        res = point_log(img);
    }
    else if (strcmp(op, "gamma") == 0)
    {
        if (param <= 0)
            param = 1.0;
        res = point_gamma(img, param);
    }
    else if (strcmp(op, "negative") == 0)
    {
        res = point_negative(img);
    }
    else
    {
        fprintf(stderr, "Unknown op: %s\n", op);
    }
    if (res)
    {
        char outp[256];
        if (strcmp(op, "gamma") == 0)
            snprintf(outp, sizeof(outp), "out/B/%s_gamma_%.2f.png", file_stem(path), param);
        else
            snprintf(outp, sizeof(outp), "out/B/%s_%s.png", file_stem(path), op);
        save_png(outp, res);
        free_image(res);
        printf("Saved %s\n", outp);
    }
    free_image(img);
}

static void cmd_resize(const char *path,
                       int out_w, int out_h,
                       const char *method)
{
    ensure_out_dir();
    Image *img = read_image(path);
    if (!img)
        img = read_raw(path, 512, 512, 1);
    if (!img)
    {
        fprintf(stderr, "Cannot read %s\n", path);
        return;
    }

    Image *res = NULL;
    if (strcmp(method, "nearest") == 0)
    {
        res = resize_nearest(img, out_w, out_h);
    }
    else if (strcmp(method, "bilinear") == 0)
    {
        res = resize_bilinear(img, out_w, out_h);
    }
    else
    {
        fprintf(stderr, "Unknown method: %s\n", method);
    }
    if (res)
    {
        char outp[256];
        snprintf(outp, sizeof(outp), "out/C/%s_resize_%dx%d_to_%dx%d_%s.png",
                 file_stem(path), img->w, img->h, out_w, out_h, method);
        save_png(outp, res);
        free_image(res);
        printf("Saved %s\n", outp);
    }
    free_image(img);
}

int main(int argc, char **argv)
{
    if (argc < 3)
    {
        fprintf(stderr,
                "Usage:\n"
                "  %s read_raw <path.raw>\n"
                "  %s read_jpg <path.jpg>\n"
                "  %s point_op <path.(jpg/png)> <log|gamma|negative> [gamma]\n"
                "  %s resize <path.(raw/jpg/png)> <in_w> <in_h> <out_w> <out_h> <nearest|bilinear>\n",
                argv[0], argv[0], argv[0], argv[0]);
        return 1;
    }
    if (strcmp(argv[1], "read_image") == 0)
    {
        cmd_read_image(argv[2]);
    }
    else if (strcmp(argv[1], "point_op") == 0)
    {
        double g = (argc >= 5) ? atof(argv[4]) : 1.0;
        cmd_point_op(argv[2], argv[3], g);
    }
    else if (strcmp(argv[1], "resize") == 0)
    {
        if (argc < 8)
        {
            fprintf(stderr, "resize args missing\n");
            return 1;
        }
        int ow = atoi(argv[5]), oh = atoi(argv[6]);
        cmd_resize(argv[2], ow, oh, argv[7]);
    }
    else
    {
        fprintf(stderr, "Unknown command.\n");
        return 1;
    }
    return 0;
}
