#!/bin/python3

"""
An image from text generator for Python 3.12 using Pillow

You can both import this file and t2i.py to use this in your project.
As well as running this or the other file as a CLI application.
However, t2i specifically implements the CLI part of the app.

MIT Copyright (c) 2024 Marco4413

https://github.com/Marco4413/Text2Image
"""

# Requires:
# - Python (3.12)
# - pillow (10.4.0)
# $ pip install pillow

from PIL import Image, ImageDraw, ImageFont, ImageFilter

import re, os.path as os_path

# Try to keep backwards compatibility with Python 3.8
from typing import Tuple, Union
Vec2      = Tuple[int,int]
RGBColor  = Tuple[int,int,int]
Alignment = Union["left","center","right"]
BaselineAlignment = Union["none","broad","perfect"]

def sanitize_filename(filename: str) -> str:
    """Replaces all path-unsafe characters from filename with safe ones."""
    def replace_with_codepoint(m: re.Match):
        ch = m.group(0)
        if ch.isspace():
            return " "
        elif ord(ch) >= 128:
            return f"U-{ord(ch)}-"
        return ""
    return re.sub(r"[^a-zA-Z0-9\. \-]", replace_with_codepoint, filename)

def px(x): return x
def pt(x): return int(x * (96.0/72.0))

def colorize_image(image: Image.Image, color: RGBColor) -> Image.Image:
    """Sets every pixel of the given image to color*average_pixel_color"""
    image_pixels = image.load()
    for i in range(image.size[0]):
        for j in range(image.size[1]):
            pixel = image_pixels[i,j]
            average_color = (pixel[0]+pixel[1]+pixel[2])/255.0
            image_pixels[i,j] = (
                int(color[0]*average_color),
                int(color[1]*average_color),
                int(color[2]*average_color),
                pixel[3]
            )
    return image

def new_image_from_text(
    text: str, *,
    # text settings
    font: ImageFont=None,
    font_size: int=None,
    padding: Vec2=(0,0),
    fill_color: RGBColor=None,
    stroke_width: int=0,
    stroke_color: RGBColor=None,
    multiline_align: Alignment="center",
    multiline_spacing: int=4,
) -> Tuple[Image.Image, int]:
    """
    Generate an image containing the specified text drawn with the specified settings.
    Coordinates and sizes are in pixels.

    **Use generate_text_image if you want to apply additional effects to the text.**

    :param str text: The text to render.
    :param font: The font to use. If None the default Pillow font is used.
    :type font: ImageFont or None
    :param font_size: The font size used if no font is provided.
    :type font_size: int or None
    :param fill_color: The color used to fill the text.
    :type fill_color: RGBColor or None
    :param int stroke_width: The width of the stroke used to draw the text.
    :param stroke_color: The color used for the stroke of the text.
    :type stroke_color: RGBColor or None
    :param Alignment multiline_align: Alignment for lines of multi-line text.
    :param int multiline_spacing: Spacing between lines for multi-line text.

    :return: A tuple containing the Pillow image that was generated and the text descent.
             The text descent for single-line text is the distance from the bottom of the image to the baseline.
             For multi-line text it's the distance to the baseline of the first line.
    :rtype: (Image.Image, int)
    """
    # get bbox for text
    image = Image.new("RGBA", (0,0), (0,0,0,0))
    draw = ImageDraw.Draw(image)
    (left, top, right, bottom) = draw.multiline_textbbox(
        (0,0), text,
        align=multiline_align,
        anchor="ms",
        font=font, font_size=font_size,
        stroke_width=stroke_width,
        spacing=multiline_spacing,
    )

    # FOR SOME REASON bbox MAY CONTAIN 0.0 WHICH IS A FLOAT... WHY???
    x = int(-left)
    y = int(-top)
    width = int(right-left)
    height = int(bottom-top)

    # resize image to fit text
    image = image.resize((width, height))
    draw = ImageDraw.Draw(image)
    draw.multiline_text(
        (x,y), text,
        align=multiline_align,
        anchor="ms",
        font=font, font_size=font_size,
        stroke_width=stroke_width,
        spacing=multiline_spacing,
        fill=fill_color, stroke_fill=stroke_color,
    )
    return (image, int(bottom))

def generate_text_image(
    text: str, *,
    # text settings
    font: ImageFont=None,
    font_size: int=None,
    fill_color: RGBColor=None,
    stroke_width: int=0,
    stroke_color: RGBColor=None,
    multiline_align: Alignment="center",
    multiline_spacing: int=4,
    # post-processing
    baseline_align: BaselineAlignment="none",
    background_color: RGBColor=None,
    shadow_color: RGBColor=None,
    shadow_offset: Vec2=(0,0),
    shadow_blur: float=0.0, # if <= 0.0 it's disabled, ImageFilter.BoxBlur is used
    # output settings
    padding: Vec2=(0,0),
    aspect_ratio: float=-1.0,
    min_size: Vec2=None,
) -> Image.Image:
    """
    Generate an image containing the specified text drawn with the specified settings.
    Coordinates and sizes are in pixels.

    :param str text: The text to render.
    :param font: The font to use. If None the default Pillow font is used.
    :type font: ImageFont or None
    :param font_size: The font size used if no font is provided.
    :type font_size: int or None
    :param fill_color: The color used to fill the text.
    :type fill_color: RGBColor or None
    :param int stroke_width: The width of the stroke used to draw the text.
    :param stroke_color: The color used for the stroke of the text.
    :type stroke_color: RGBColor or None
    :param Alignment multiline_align: Alignment for lines of multi-line text.
    :param int multiline_spacing: Spacing between lines for multi-line text.
    :param background_color: The color for the background of the generated image. If None, it's transparent.
    :type background_color: RGBColor or None
    :param shadow_color: The color for the text shadow. If None, no shadow is generated.
    :type shadow_color: RGBColor or None
    :param Vec2 shadow_offset: Offset used for the text shadow.
    :param float shadow_blur: Intensity of the blur applied to the text shadow. If 0, none is applied.
    :param Vec2 padding: The minimum padding around the text.
    :param aspect_ratio: The aspect ratio of the resulting image. If <= 0, the image is shrunk to fit the text+padding.
    :type aspect_ratio: float or None
    :param min_size: If the image is smaller in width or height than the ones provided then it's expanded to those.
    :type min_size: Vec2 or None

    :return: The Pillow image that was generated.
    :rtype: Image.Image
    """
    (text_image, text_descent) = new_image_from_text(
        text,
        font=font, font_size=font_size,
        stroke_width=stroke_width,
        multiline_align=multiline_align,
        multiline_spacing=multiline_spacing,
        fill_color=fill_color,
        stroke_color=stroke_color,
    )

    # any((c in "\r\n") for c in text)
    # Pillow does not treat \r as new line
    is_multiline = "\n" in text
    if is_multiline:
        # Has no meaning for multiline text
        text_descent = 0

    shadow = None
    if shadow_color is not None:
        shadow = colorize_image(text_image.copy(), shadow_color)

    x = 0
    y = 0
    width = text_image.width
    height = text_image.height
    if shadow is not None:
        if shadow_offset[0] >= 0:
            width += shadow_offset[0]
        else:
            x -= shadow_offset[0]
            width -= shadow_offset[0]

        if shadow_offset[1] >= 0:
            height += shadow_offset[1]
        else:
            y -= shadow_offset[1]
            height -= shadow_offset[1]

    if min_size is not None:
        (min_width, min_height) = min_size
        if width < min_width:
            x += (min_width-width)//2
            width = min_width
        if height <= min_height:
            y += (min_height-height)//2
            height = min_height
        if aspect_ratio is None and min_height != 0:
            aspect_ratio = min_width/min_height

    if not is_multiline:
        # I hate the match statement, indentation gets out of hand quickly
        if baseline_align == "broad":
            y += text_descent//2
        elif baseline_align == "perfect":
            baseline_offset = text_descent-text_image.height//2
            y += baseline_offset
        else:
            assert baseline_align == "none"

    if aspect_ratio is not None and aspect_ratio > 0.0:
        desired_width = max(int(height*aspect_ratio), width)
        desired_height = max(int(width/aspect_ratio), height)
        if desired_width > desired_height:
            assert desired_width >= width
            x += (desired_width-width)//2
            width = desired_width

            new_height = int(desired_width/aspect_ratio)
            y += (new_height-height)//2
            height = new_height
        else:
            assert desired_height >= height
            y += (desired_height-height)//2
            height = desired_height

            new_width = int(desired_height*aspect_ratio)
            x += (new_width-width)//2
            width = new_width

    # If we're not respecting padding or we're out of bounds, expand
    if y <= padding[1]:
        y = padding[1]
    y_end = y+text_image.height
    if height-y_end < padding[1]:
        height = y_end+padding[1]

    if x <= padding[0]:
        x = padding[0]
    x_end = x+text_image.width
    if width-x_end < padding[0]:
        width = x_end+padding[0]

    if background_color is None:
        background_color = (0,0,0,0)
    else:
        background_color = (*background_color, 255)

    image = Image.new("RGBA", (width, height), background_color)
    draw = ImageDraw.Draw(image)
    
    if shadow is not None:
        image.alpha_composite(shadow, (x+shadow_offset[0],y+shadow_offset[1]))
        if shadow_blur >= 0.0:
            image = image.filter(ImageFilter.BoxBlur(shadow_blur))

    image.alpha_composite(text_image, (x,y))
    return image

def generate_and_save_text_image(
    text: str, *,
    out_directory: str=None,
    out_filename: str=None,
    **kwargs
) -> Image.Image:
    """
    Generate an image with generate_text_image and save it as a png.

    :param str text: The text to render.
    :param out_directory: The output directory. If None the cwd is used.
    :type out_directory: str or None
    :param out_filename: The output file name. If None it's extracted from text.
    :type out_filename: str or None
    :param **kwargs: All other keyword arguments are passed directly to generate_text_image.

    :return: The Pillow image that was saved.
    :rtype: Image.Image
    """
    image = generate_text_image(text, **kwargs)
    filename = out_filename
    if filename is None:
        filename = sanitize_filename(text)
        if not filename.endswith(".png"):
            filename += ".png"
    fullpath = os_path.join(out_directory, filename) if out_directory is not None else filename
    image.save(fullpath, format="png")
    return image

if __name__ == "__main__":
    from t2i import __main__
    from sys import argv
    __main__(argv.copy())
