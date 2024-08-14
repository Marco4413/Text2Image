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

# With background
$ ./t2i.py -fs 96pt -size 1280,640 -bg 0x222A30 -fg 0xE6E2E1 -sh 0x010704 -sho=-30,15 -shb 10 -- Text2Image
```

### Center-aligned Characters

Here's an example of aligned chars generation:
```sh
# Generate e f g perfectly aligned
$ ./t2i.py -fs 32pt -size 32,64 -baseline perfect -- e f g

# Generate e f g broadly aligned
$ ./t2i.py -fs 32pt -size 32,64 -baseline broad -- e f g

# Generate e f g center-aligned based on char size
$ ./t2i.py -fs 32pt -size 32,64 -baseline none -- e f g
```

Specifying a min-size (`-size`) is important, and you should check
that the output image was not expanded. If all images have the same
size specified in the command, then you can tile them to write text.

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
