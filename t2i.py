#!/bin/python3

"""
An image from text generator for Python 3.12 using Pillow

You can both import this file and text2image.py to use this in your project.
As well as running this or the other file as a CLI application.
However, this one specifically implements the CLI part of the app.
Therefore, by importing this, you'll also import some arg conversion functions.

MIT Copyright (c) 2024 Marco4413

https://github.com/Marco4413/Text2Image
"""

# Requires:
# - Python (3.12)
# - pillow (10.4.0)
# $ pip install pillow

from text2image import *

def get_measure_format() -> str:
    return "<PIXELS | Npx | Npt>"

def any_measure_type(measure: str) -> int:
    if measure.endswith("px"):
        val = int(measure[:-2])
        return px(val)
    elif measure.endswith("pt"):
        val = int(measure[:-2])
        return pt(val)
    return int(measure)

def measure_type(measure: str) -> int:
    val = any_measure_type(measure)
    if val < 0:
        raise ValueError("Measure must be non-negative.")
    return val

def get_ratio_format() -> str:
    return "<N | N/D>"

def ratio_type(ratio_str: str) -> float:
    ratio_comps = [float(x) for x in ratio_str.split("/")]
    if len(ratio_comps) == 1:
        return ratio_comps[0]
    elif len(ratio_comps) == 2:
        if ratio_comps[1] == 0.0:
            raise ValueError("Ratio has division by 0.")
        return ratio_comps[0]/ratio_comps[1]
    raise ValueError("Ratio must be either a float or a pair of floats separated by /.")

def get_vec2_format() -> str:
    # TODO: Maybe use measure format? Though it would make the tip WAY longer.
    return "<X,Y>"

def vec2_type(vec2_str: str) -> Vec2:
    vec2 = tuple(any_measure_type(x) for x in vec2_str.split(","))
    if len(vec2) != 2:
        raise ValueError("A Vec2 is a pair of comma-separated measures.")
    return vec2

def positive_vec2_type(vec2_str: str) -> Vec2:
    # I know that positive is strictly > 0 but this also accepts 0s.
    # The name would have been too long for my likings.
    vec2 = tuple(measure_type(x) for x in vec2_str.split(","))
    if len(vec2) != 2:
        raise ValueError("A non-negative Vec2 is a pair of comma-separated positive measures.")
    return vec2

def get_color_format() -> str:
    return "<R,G,B | 0xL | 0xLL | 0xRGB | 0xRRGGBB>"

def color_type(color_str: str) -> RGBColor:
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

def get_alignment_format() -> str:
    return "<left | center | right>"

def alignment_type(alignment_str: str) -> Alignment:
    if alignment_str not in ["left","center","right"]:
        raise ValueError("Alignment must be one of 'left', 'center' or 'right'.")
    return alignment_str

def __main__(argv):
    import argparse, os

    program = argv.pop(0)
    arg_parser = argparse.ArgumentParser(
        prog=program,
        description="A Text to Image generator.",
    )

    arg_parser.add_argument("text", help="The text to generate an image of.", nargs="+")
    arg_parser.add_argument("-outdir", "--out-directory", type=str, metavar="OUT_DIRECTORY", default=".", help="the output directory for the generated images (default: cwd)")

    font_path = os.path.join(os.path.dirname(__file__), "JetBrainsMono.ttf")
    arg_parser.add_argument("-ff", "--font-family", type=str, metavar="FONT_FAMILY", default=font_path, help="the font family to use (default: JetBrainsMono)")
    arg_parser.add_argument("-fs", "--font-size", type=measure_type, metavar=get_measure_format(), default="32pt", help="the font size to use (default: %(default)s)")
    arg_parser.add_argument("-fg", "--fill-color", type=color_type, metavar=get_color_format(), default="0xE6E2E1", help="the color to fill the text with (default: %(default)s)")
    arg_parser.add_argument("-stw", "--stroke-width", type=measure_type, metavar=get_measure_format(), default="0px", help="the width of the stroke used to draw the text (default: %(default)s)")
    arg_parser.add_argument("-st", "--stroke-color", type=color_type, metavar=get_color_format(), help="the color of the stroke used to draw the text (default: %(default)s)")
    # TODO: Use choices?
    arg_parser.add_argument("-align", "--multiline-align", type=alignment_type, metavar=get_alignment_format(), default="center", help="the alignment used for multiline text (default: %(default)s)")
    arg_parser.add_argument("-spacing", "--multiline-spacing", type=any_measure_type, metavar=get_measure_format(), default="4px", help="the spacing between lines in multiline text. may be a negative value (default: %(default)s)")

    arg_parser.add_argument("-bg", "--background-color", type=color_type, metavar=get_color_format(), help="the color used as the background of the image (default: %(default)s)")
    arg_parser.add_argument("-sh", "--shadow-color", type=color_type, metavar=get_color_format(), help="the color used for text shadows (default: %(default)s)")
    arg_parser.add_argument("-sho", "--shadow-offset", type=vec2_type, metavar=get_vec2_format(), default="0,0", help="the offset of the text shadow (default: %(default)s)")
    arg_parser.add_argument("-shb", "--shadow-blur", type=float, metavar="SHADOW_BLUR", default=-1.0, help="the intensity of the blur applied to the text shadow. none if <= 0 (default: %(default)s)")

    arg_parser.add_argument("-pad", "--padding", type=positive_vec2_type, metavar=get_vec2_format(), default="0,0", help="the padding applied between the text and the border of the image (default: %(default)s)")
    arg_parser.add_argument("-aspect", "--aspect-ratio", type=ratio_type, metavar=get_ratio_format(), help="the desired aspect ratio of the output image. fit to text if <= 0 or None. calculated from min-size if provided and aspect-ratio is None (default: %(default)s)")
    arg_parser.add_argument("-size", "--min-size", type=positive_vec2_type, metavar=get_vec2_format(), help="the minimum size of the image. if the text does not fit, the image is expanded (default: %(default)s)")

    if len(argv) == 0:
        arg_parser.print_help()
        return
    opt = arg_parser.parse_args(argv)

    if opt.out_directory is not None:
        if not os.path.exists(opt.out_directory):
            try:
                os.makedirs(opt.out_directory, exist_ok=True)
            except:
                print(f"Could not generate output directory '{opt.out_directory}'.");
                return

    font = None
    try:
        font = ImageFont.truetype(opt.font_family, opt.font_size)
    except OSError:
        print(f"Could not load font '{opt.font_family}'.")
        return

    for text in opt.text:
        def replace_escape_seq(m: re.Match) -> str:
            seq = m.group(1)
            if seq == "n": return "\n"
            return seq
        text = re.sub(r"\\([\\n])", replace_escape_seq, text)

        filename = sanitize_filename(text).strip(".")
        if not filename.endswith(".png"):
            filename += ".png"
        filepath = os.path.join(opt.out_directory, filename)
        print(f"Generating '{filepath}'...")

        generate_text_image(
            text,
            font=font,
            fill_color=opt.fill_color,
            stroke_width=opt.stroke_width,
            stroke_color=opt.stroke_color,
            multiline_align=opt.multiline_align,
            multiline_spacing=opt.multiline_spacing,
            background_color=opt.background_color,
            shadow_color=opt.shadow_color,
            shadow_offset=opt.shadow_offset,
            shadow_blur=opt.shadow_blur,
            padding=opt.padding,
            aspect_ratio=opt.aspect_ratio,
            min_size=opt.min_size,
        ).save(filepath, format="png")
    print(f"Generated all {len(opt.text)} files.")

if __name__ == "__main__":
    from sys import argv
    __main__(argv.copy())
