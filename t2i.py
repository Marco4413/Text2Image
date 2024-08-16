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
    return "<transparent | R,G,B | 0xL | 0xLL | 0xRGB | 0xRRGGBB>"

def get_alignment_format() -> str:
    return "<left | center | right>"

def get_baseline_format() -> str:
    return "<none | broad | perfect>"

def __main__(argv) -> int:
    import argparse, os, traceback
    from datetime import datetime
    from sys import stderr

    program = argv.pop(0)
    arg_parser = argparse.ArgumentParser(
        prog=program,
        usage="%(prog)s [-h | --help] [option ...] [--] text [text ...]",
        description="A Text to Image generator.",
    )

    # TODO: Do a pass of help prompts and defaults
    arg_parser.add_argument("text", help="the text to generate an images of. each text is put into its own file based on out-filename", nargs="+")
    arg_parser.add_argument("-outdir", "--out-directory", type=str, metavar="<OUT_DIRECTORY>", default=".", help="the output directory for the generated images (default: '%(default)s')")
    arg_parser.add_argument("-outfile", "--out-filename", type=str, metavar="<OUT_FILENAME>", default="{default_filename}", help="the output filename template for each text (default: '%(default)s')")

    font_path = os.path.join(os.path.dirname(__file__), "JetBrainsMono.ttf")
    arg_parser.add_argument("-ff", "--font-family", type=str, metavar="<FONT_FAMILY>", default=font_path, help="the font family to use. can also be a path to a truetype font file (default: 'JetBrainsMono.ttf')")
    arg_parser.add_argument("-fs", "--font-size", type=measure_type, metavar=get_measure_format(), default="32pt", help="the font size to use (default: %(default)s)")
    arg_parser.add_argument("-fg", "--fill-color", type=color, metavar=get_color_format(), default="0xE6E2E1", help="the color to fill the text with (default: %(default)s)")
    arg_parser.add_argument("-stw", "--stroke-width", type=measure_type, metavar=get_measure_format(), default="0px", help="the width of the stroke used to draw the text (default: %(default)s)")
    arg_parser.add_argument("-st", "--stroke-color", type=color, metavar=get_color_format(), default="transparent", help="the color of the stroke used to draw the text (default: %(default)s)")
    arg_parser.add_argument("-align", "--multiline-align", choices=["left","center","right"], metavar=get_alignment_format(), default="center", help="the alignment used for multiline text (default: %(default)s)")
    arg_parser.add_argument("-spacing", "--multiline-spacing", type=any_measure_type, metavar=get_measure_format(), default="4px", help="the spacing between lines in multiline text. may be a negative value (default: %(default)s)")

    arg_parser.add_argument("-baseline", "--baseline-align", choices=["none","broad","perfect"], metavar=get_baseline_format(), default="none", help="*DOES NOTHING FOR MULTI-LINE TEXT* the kind of alignment used to center the text based on its baseline. if 'none' it's perfectly centered based on the text height (default: %(default)s)")
    arg_parser.add_argument("-bg", "--background-color", type=color, metavar=get_color_format(), default="transparent", help="the color used as the background of the image (default: %(default)s)")
    arg_parser.add_argument("-sh", "--shadow-color", type=color, metavar=get_color_format(), default="transparent", help="the color used for text shadows (default: %(default)s)")
    arg_parser.add_argument("--no-shadow-blend", dest="shadow_color_blend", action="store_false", help="whether to blend the shadow color with the text color (default: %(default)s)")
    arg_parser.add_argument("-sho", "--shadow-offset", type=vec2_type, metavar=get_vec2_format(), default="0,0", help="the offset of the text shadow (default: %(default)s)")
    arg_parser.add_argument("-shb", "--shadow-blur", type=float, metavar="<SHADOW_BLUR>", default=-1.0, help="the intensity of the blur applied to the text shadow. none if <= 0 (default: %(default)s)")

    arg_parser.add_argument("-padx", "--padding-x", dest="padx", type=positive_vec2_type, metavar="<L,R>", default="0,0", help="the horizontal padding applied to the left and right of the text (default: %(default)s)")
    arg_parser.add_argument("-pady", "--padding-y", dest="pady", type=positive_vec2_type, metavar="<T,B>", default="0,0", help="the vertical padding applied to the top and bottom of the text (default: %(default)s)")
    arg_parser.add_argument("-pad", "--padding", type=positive_vec2_type, metavar=get_vec2_format(), default=None, help="this setting overrides padx and pady. sets both horizontal and vertical padding")
    arg_parser.add_argument("-aspect", "--aspect-ratio", type=ratio_type, metavar=get_ratio_format(), help="the desired aspect ratio of the output image. fit to text if <= 0 or None. calculated from min-size if provided and aspect-ratio is None (default: %(default)s)")
    arg_parser.add_argument("-size", "--min-size", type=positive_vec2_type, metavar=get_vec2_format(), help="the minimum size of the image. if the text does not fit, the image is expanded (default: %(default)s)")

    if len(argv) == 0:
        arg_parser.print_usage()
        return 0
    opt = arg_parser.parse_args(argv)

    if opt.out_directory is not None:
        if not os.path.exists(opt.out_directory):
            try:
                os.makedirs(opt.out_directory, exist_ok=True)
            except:
                print(f"ERROR: Could not generate output directory '{opt.out_directory}'.", file=stderr);
                return 1

    font = None
    try:
        font = ImageFont.truetype(opt.font_family, opt.font_size)
    except OSError:
        print(f"ERROR: Could not load font '{opt.font_family}'.", file=stderr)
        return 1

    today = datetime.today()
    for idx in range(len(opt.text)):
        text = opt.text[idx]
        def replace_escape_seq(m: re.Match) -> str:
            seq = m.group(1)
            if seq == "n": return "\n"
            return seq
        text = re.sub(r"\\([\\n])", replace_escape_seq, text)

        assert opt.out_filename is not None
        filename = opt.out_filename.format(
            idx=idx, default_filename=sanitize_filename(text).strip("."),
            year=today.year, month=today.month, day=today.day,
            hour=today.hour, minute=today.minute, second=today.second,
        )

        if not filename.endswith(".png"):
            filename += ".png"
        filepath = os.path.join(opt.out_directory, filename)
        print(f"Generating '{filepath}'...")

        try:
            generate_text_image(
                text,
                font=font,
                fill_color=opt.fill_color,
                stroke_width=opt.stroke_width,
                stroke_color=opt.stroke_color,
                multiline_align=opt.multiline_align,
                multiline_spacing=opt.multiline_spacing,
                baseline_align=opt.baseline_align,
                background_color=opt.background_color,
                shadow_color=opt.shadow_color,
                shadow_color_blend=opt.shadow_color_blend,
                shadow_offset=opt.shadow_offset,
                shadow_blur=opt.shadow_blur,
                padx=opt.padx,
                pady=opt.pady,
                padding=opt.padding,
                aspect_ratio=opt.aspect_ratio,
                min_size=opt.min_size,
            ).save(filepath, format="png")
        except:
            print(f"ERROR: Could not generate '{filepath}'.", file=stderr)
            traceback.print_exc(file=stderr)
            return 1
    print(f"Generated all {len(opt.text)} files.")
    return 0

if __name__ == "__main__":
    from sys import argv, exit
    exit(__main__(argv.copy()))
