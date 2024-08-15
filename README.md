# ![Text2Image](logo_transparent.png)

A CLI (and Python module) which generates an image from text.

## What's the point of this project?

I was looking at some watchface maker for a smartwatch brand,
and I saw that EVERY digit had to be a separate image.

Doing that for every piece of text would have taken me ages to make.

So, instead of using [GIMP](https://www.gimp.org), I decided to
create this Python script which uses [Pillow](https://github.com/python-pillow/Pillow)
to generate an image from any kind of text.

If you generate single characters and specify a fixed min size
which fits each one, they should all be aligned with each other.
That means that you can just generate an image of W*chars by H
and put the characters next to each other to write text.

See [Center-Aligned Characters](#center-aligned-characters)

## Usage

Make sure to read the [requirements](#requirements) section first.

This project can be both used as a CLI tool or imported from other Python scripts.

To install this, download the repo and extract all files in the same directory.

The following command will print the help prompt for the CLI:
```sh
$ ./t2i.py --help
```

You may also run `text2image.py` which will import `t2i.py` and run that instead.

If you want to see an example of usage from other Python scripts
see the [test.py](./test.py) script. All functions use the
[Sphinx](https://www.sphinx-doc.org/en/master/) syntax for
documenting their usage.

### Logo Generation

```sh
# Transparent background
$ ./t2i.py -fs 96pt -size 1280,640 -fg 0xE6E2E1 -st 0x222A30 -stw 2px -sh 0x010704 -sho=-30,15 -shb 10 -- Text2Image

# Hollow with background
$ ./t2i.py -fs 96pt -size 1280,640 -bg 0x222A30 -fg transparent -st 0xE6E2E1 -stw 2px -sh 0x010704 -sho=-30,15 -shb 20 -- Text2Image

# With background
$ ./t2i.py -fs 96pt -size 1280,640 -bg 0x222A30 -fg 0xE6E2E1 -sh 0x010704 -sho=-30,15 -shb 10 -- Text2Image
```

### Center-aligned Characters

Here's an example of aligned chars generation:
```sh
# Generate e f g perfectly aligned
$ ./t2i.py -fs 32pt -size 0,64 -pad 3,0 -baseline perfect -- e f g

# Generate e f g broadly aligned
$ ./t2i.py -fs 32pt -size 0,64 -pad 3,0 -baseline broad -- e f g

# Generate e f g center-aligned based on char size
$ ./t2i.py -fs 32pt -size 0,64 -pad 3,0 -baseline none -- e f g
```

Specifying a min height (`-size 0,H`) is important since the default behaviour
is shrink to fit the text + padding. You should make sure the text fits the
specified height, otherwise, the text position is clamped to not go out of bounds.
Therefore, the baseline is not perfectly centered vertically.

Since the specified min width is 0 the image is shrunk to fit
horizontally. However, we can add some padding to keep some distance
between the characters. If you want vertical padding, it's better
to increase the min height so you see whether the text is going out of
bounds or not (if its top edge is right at the top of the image,
it's probably going out of bounds).

`none` center aligns the text based on its bounding box. This is
the default behaviour for text generation.

`broad` does an approximation of center-alignment based on the text
baseline. You should use this if you want to keep the height of the
image small.

`perfect` perfectly aligns to the center the text based on its baseline.
This has the drawback of generating very tall images to fit the text.

## What's up with the two main python files?

1. `text2image.py` is the actual module that provides all the functions to generate images.
2. `t2i.py` contains the CLI logic.

You can import either of them when developing a Python script
that uses this project. However, `t2i.py` also includes some string
to type conversion for types used in the library.

When `text2image.py` is ran as main, it will actually import and run
`t2i.py` passing all arguments provided.

Basically, if you want to develop a Python script, you should import
`text2image.py` if you don't want to depend on two files.

## Requirements

This project was developed for Python 3.12

You'll also need the following Python modules:
- pillow 10.4.0

`$ pip install Pillow`
