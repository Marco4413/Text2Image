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

def color(color_str: str) -> Union[RGBColor, None]:
    """
    Converts a string into an RGB color.

    Allowed formats are <transparent | R,G,B | 0xL | 0xLL | 0xRGB | 0xRRGGBB> where hex values may also start with a '#'.

    :param str color_str: The string to convert from.
    :return: RGBColor if the specified color is not 'transparent', None otherwise.
    :rtype: RGBColor or None
    """
    if color_str == "transparent":
        return None

    if color_str.startswith("#") or color_str.startswith("0x"):
        hex_str = color_str[1:] if color_str.startswith("#") else color_str[2:]
        if len(hex_str) == 1:
            l = int(hex_str, base=16)
            return (l * 0x11, l * 0x11, l * 0x11)
        elif len(hex_str) == 2:
            ll = int(hex_str, base=16)
            return (ll, ll, ll)
        elif len(hex_str) == 3:
            rgb = int(hex_str, base=16)
            return (
                ((rgb & 0xF00) >> 8) * 0x11,
                ((rgb & 0x0F0) >> 4) * 0x11,
                ((rgb & 0x00F) >> 0) * 0x11,
            )
        elif len(hex_str) == 6:
            rrggbb = int(hex_str, base=16)
            return (
                (rrggbb & 0xFF0000) >> 16,
                (rrggbb & 0x00FF00) >>  8,
                (rrggbb & 0x0000FF) >>  0,
            )
        raise ValueError("An hex color must have either 1, 2, 3 or 6 digits.")

    rgb_color = tuple(int(x) for x in color_str.split(","))
    if len(rgb_color) != 3:
        raise ValueError("A color is a triple of comma-separated positive integers RGB values in the range of [0,255].")
    for comp in rgb_color:
        if comp < 0 or comp > 255:
            raise ValueError("A color is a triple of comma-separated positive integers RGB values in the range of [0,255].")
    return rgb_color

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
    fill_color: Union[RGBColor, None]=(0,0,0),
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
    :param fill_color: The color used to fill the text. Transparent if None.
    :type fill_color: RGBColor or None
    :param int stroke_width: The width of the stroke used to draw the text.
    :param stroke_color: The color used for the stroke of the text. Transparent if None.
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
        fill=(0,0,0,0) if fill_color is None else fill_color,
        stroke_fill=(0,0,0,0) if stroke_color is None else stroke_color,
    )
    return (image, int(bottom))

def generate_text_image(
    text: str, *,
    # text settings
    font: ImageFont=None,
    font_size: int=None,
    fill_color: Union[RGBColor, None]=(0,0,0),
    stroke_width: int=0,
    stroke_color: RGBColor=None,
    multiline_align: Alignment="center",
    multiline_spacing: int=4,
    # post-processing
    baseline_align: BaselineAlignment="none",
    background_color: RGBColor=None,
    shadow_color: RGBColor=None,
    shadow_color_blend: bool=True,
    shadow_offset: Vec2=(0,0),
    shadow_blur: float=0.0, # if <= 0.0 it's disabled, ImageFilter.BoxBlur is used
    # output settings
    padx: Vec2=(0,0),
    pady: Vec2=(0,0),
    padding: Vec2=None,
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
    :param fill_color: The color used to fill the text. Transparent if None.
    :type fill_color: RGBColor or None
    :param int stroke_width: The width of the stroke used to draw the text.
    :param stroke_color: The color used for the stroke of the text. Transparent if None.
    :type stroke_color: RGBColor or None
    :param Alignment multiline_align: Alignment for lines of multi-line text.
    :param int multiline_spacing: Spacing between lines for multi-line text.
    :param BaselineAlignment baseline_align: Vertical alignment used for single-line text.
    :param background_color: The color for the background of the generated image. Transparent if None.
    :type background_color: RGBColor or None
    :param shadow_color: The color for the text shadow. If None, no shadow is generated.
    :type shadow_color: RGBColor or None
    :param bool shadow_color_blend: Whether to blend shadow_color with the text color.
    :param Vec2 shadow_offset: Offset used for the text shadow.
    :param float shadow_blur: Intensity of the blur applied to the text shadow. If 0, none is applied.
    :param Vec2 padx: The horizontal padding around the text (left, right).
    :param Vec2 pady: The vertical padding around the text (top, bottom).
    :param padding: The padding around the text (horizontal, vertical). If specified padx and pady are overridden.
    :type padding: Vec2 or None
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
        # Can't check for shadow_offset != (0,0) because the shadow may be blurred
        if shadow_color_blend:
            shadow = colorize_image(text_image.copy(), shadow_color)
        else:
            (shadow, _) = new_image_from_text(
                text,
                font=font, font_size=font_size,
                stroke_width=stroke_width,
                multiline_align=multiline_align,
                multiline_spacing=multiline_spacing,
                fill_color=shadow_color,
                stroke_color=shadow_color,
            )
    else:
        # Set shadow_offset to 0 so we can safely use it when no shadow is present
        shadow_offset = (0,0)

    if padding is not None:
        padx = (padding[0], padding[0])
        pady = (padding[1], padding[1])

    x = padx[0]
    y = pady[0]
    width = text_image.width + padx[0]+padx[1]
    height = text_image.height + pady[0]+pady[1]
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

    # Up to here everything is centered around the text+shadow
    # Moreover, the width and height of the image is fully calculated
    # So here's the place where we can change the vertical alignment of the text
    if not is_multiline:
        baseline_offset = 0
        if baseline_align == "broad":
            baseline_offset = text_descent//2
        elif baseline_align == "perfect":
            baseline_offset = text_descent-text_image.height//2
        elif baseline_align != "none":
            raise ValueError("baseline_align must be 'broad', 'perfect' or 'none'.")

        # If 'none' running the code below should do nothing
        # Even though they're not heavy calculations,
        #  I just want to make sure they do not interfere
        #  with the output image in any way
        if baseline_align != "none":
            # Calculate lower and upper bounds
            # Min and Max y values to keep the text+shadow within bounds+padding
            lower_bounds = pady[0] - min(0, shadow_offset[1])
            upper_bounds = height - (pady[1]+text_image.height+max(0, shadow_offset[1]))

            new_y = y+baseline_offset
            # Clamp new_y between lower_bounds and upper_bounds
            y = min(max(new_y, lower_bounds), upper_bounds)

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
