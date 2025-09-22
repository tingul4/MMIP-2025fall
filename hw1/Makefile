CC := cc
CFLAGS := -O2 -Wall -Wextra -std=c11
LDFLAGS := -lm

SRC := src/main.c src/image.c
HDR := src/image.h src/stb_image.h src/stb_image_write.h

all: dip_tool

dip_tool: $(SRC) $(HDR)
	$(CC) $(CFLAGS) -o $@ $(SRC) $(LDFLAGS)

run-read-jpg:
	./dip_tool read_jpg boat.jpg

clean:
	rm -f dip_tool
	rm -rf out
