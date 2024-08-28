#!/usr/bin/env python3

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

import argparse as _argparse

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

class _CustomHelpFormatter(_argparse.HelpFormatter):
    """Custom HelpFormatter from argparse which fits the needs of t2i's CLI"""

    # Copied from the base class and changed choices formatting.
    def _metavar_formatter(self, action, default_metavar):
        if action.metavar is not None:
            result = action.metavar
        elif action.choices is not None:
            choice_strs = [str(choice) for choice in action.choices]
            result = '<%s>' % ' | '.join(choice_strs)
        else:
            result = default_metavar

        def format(tuple_size):
            if isinstance(result, tuple):
                return result
            else:
                return (result, ) * tuple_size
        return format
    # Copied from the base class method. The only change is metavars only being shown for the full option:
    # -fg, --fill-color <transparent | R,G,B | 0xL | 0xLL | 0xRGB | 0xRRGGBB>
    # Which is cleaner when metavars explain the format of the var.
    def _format_action_invocation(self, action: _argparse.Action) -> str:
        from typing import List
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            metavar, = self._metavar_formatter(action, default)(1)
            return metavar
        else:
            parts: List[str] = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)
            # if the Optional takes a value, format is:
            #    -s, --long ARGS
            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    if option_string.startswith("--"):
                        parts.append("%s %s" % (option_string, args_string))
                    else:
                        parts.append(option_string)
            return ", ".join(parts)
    # Copied from _argparse.ArgumentDefaultsHelpFormatter.
    # This won't emit the default if it's None or a bool.
    def _get_help_string(self, action: _argparse.Action) -> str:
        import textwrap
        help = "" if action.help is None else textwrap.dedent(action.help).strip()
        if (action.default is not _argparse.SUPPRESS
            and action.default is not None
            and not isinstance(action, _argparse._StoreConstAction)
            and "default:" not in help
        ):
            defaulting_nargs = [_argparse.OPTIONAL, _argparse.ZERO_OR_MORE]
            if action.option_strings or action.nargs in defaulting_nargs:
                help += "\n(default: %(default)s)"
        return help
    # Based on _argparse.RawDescriptionHelpFormatter
    # This seems the only method that handles descriptions?
    def _fill_text(self, text: str, width: int, indent: str) -> str:
        return "\n".join(indent + line.strip() for line in text.splitlines())
    def _split_lines(self, text: str, width: int) -> list:
        import textwrap
        def count_indent(text: str) -> int:
            count = 0
            for ch in text:
                if not ch.isspace(): break
                count += 1
            return count
        text_lines = []
        for line in textwrap.dedent(text).strip().splitlines():
            line_indent = count_indent(line)
            wrapped_lines = textwrap.wrap(line, width, subsequent_indent=(" " * line_indent))
            text_lines.extend(wrapped_lines)
        text_lines.append("")
        return text_lines

def __main__(argv) -> int:
    import os, traceback
    from datetime import datetime
    from sys import stderr

    program = os.path.basename(argv.pop(0))
    arg_parser = _argparse.ArgumentParser(
        prog=program,
        usage="%(prog)s [-h | --help] [option ...] [--] text [text ...]",
        description="""
            A Text to Image generator.

            A bunch of images can be generated with a single command:
            $ %(prog)s -outdir out -- 0 1 2 3 4 5 6 7 8 9

            All options are applied to all images.
        """,
        formatter_class=_CustomHelpFormatter,
    )

    arg_parser.add_argument("text", help="the text to generate images of.\neach text is put into its own file based on out-filename.\nthe following escape sequences can be used in the text: \\n, \\\\", nargs="+")
    arg_parser.add_argument("-outdir", "--out-directory", type=str, metavar="<OUT_DIRECTORY>", default=".", help="the output directory for the generated images\n(default: '%(default)s')")
    arg_parser.add_argument("-outfile", "--out-filename", type=str, metavar="<OUT_FILENAME>", default="{default_filename}", help="""
        the output filename template for each text.
        the '.png' extension is appended to the name if not already specified.
        you can use the following variables within the template:
            - {idx} the index at which the text was provided
            - {default_filename} the default name provided to the text (a version of the text where all special characters are stripped out)
            - {year}, {month}, {day}, {hour}, {minute}, {second} the date at which the COMMAND was ran (not at which the text was generated)
        e.g. 'char_{default_filename}'
        (default: '%(default)s')
    """)

    font_path = os.path.join(os.path.dirname(__file__), "JetBrainsMono.ttf")
    arg_parser.add_argument("-ff", "--font-family", type=str, metavar="<FONT_FAMILY>", default=font_path, help="the font family to use.\ncan also be a path to a truetype font file\n(default: '%(default)s')")
    arg_parser.add_argument("-fs", "--font-size", type=measure_type, metavar=get_measure_format(), default="32pt", help="the font size to use")
    arg_parser.add_argument("--no-ligatures", dest="ligatures", action="store_false", help=f"disable font ligatures. if libraqm is not available, ligatures are disabled by default.\nlibraqm:{'' if is_libraqm_available() else ' not'} available")
    arg_parser.add_argument("-fg", "--fill-color", type=color, metavar=get_color_format(), default="0xE6E2E1", help="the color to fill the text with")
    arg_parser.add_argument("-stw", "--stroke-width", type=measure_type, metavar=get_measure_format(), default="0px", help="the width of the stroke used to draw the text")
    arg_parser.add_argument("-st", "--stroke-color", type=color, metavar=get_color_format(), default="transparent", help="the color of the stroke used to draw the text")
    arg_parser.add_argument("-align", "--multiline-align", choices=("left","center","right"), default="center", help="the alignment used for multiline text")
    arg_parser.add_argument("-spacing", "--multiline-spacing", type=any_measure_type, metavar=get_measure_format(), default="4px", help="the spacing between lines in multiline text.\nmay be a negative value")

    arg_parser.add_argument("-baseline", "--baseline-align", choices=("none","broad","perfect"), default="none", help="""
        * DOES NOTHING FOR MULTI-LINE TEXT
        * THIS SETTING MUST BE USED WITH THE min-size SETTING
        the kind of alignment used to center the text based on its baseline.
            none    - centered based on the full height of the text
            broad   - centered based on the part of the text above the baseline
            perfect - the baseline of the text is at the center of the image
        the position of the text is ultimately clamped to stay within the image, make sure to have enough space to fit the text
    """)
    arg_parser.add_argument("-bg", "--background-color", type=color, metavar=get_color_format(), default="transparent", help="the color used as the background of the image")
    arg_parser.add_argument("-sh", "--shadow-color", type=color, metavar=get_color_format(), default="transparent", help="the color used for text shadows")
    arg_parser.add_argument("--no-shadow-blend", dest="shadow_color_blend", action="store_false", help="disables blending the shadow color with the text color")
    arg_parser.add_argument("--shadow-blend-method", dest="shadow_color_blend_method", choices=("grayscale+","grayscale","luminance"), default="grayscale+", help="""
        * DOES NOTHING IF no-shadow-blend IS SPECIFIED
        the method to use for blending the shadow color with the text color.
            grayscale+ - blends with a brighter grayscale of the text
            grayscale  - blends with the pure grayscale of the text
            luminance  - blends with the luminance of the text
        blending is currently done on a pixel basis and not with some average of the whole text
    """)
    arg_parser.add_argument("-sho", "--shadow-offset", type=vec2_type, metavar=get_vec2_format(), default="0,0", help="the offset of the text shadow")
    arg_parser.add_argument("-shb", "--shadow-blur", type=float, metavar="<SHADOW_BLUR>", default=0.0, help="the intensity of the blur applied to the text shadow.\nnone if <= 0")

    arg_parser.add_argument("-padx", "--padding-x", dest="padx", type=positive_vec2_type, metavar="<L,R>", default="0,0", help="the horizontal padding applied to the left and right of the text")
    arg_parser.add_argument("-pady", "--padding-y", dest="pady", type=positive_vec2_type, metavar="<T,B>", default="0,0", help="the vertical padding applied to the top and bottom of the text")
    arg_parser.add_argument("-pad", "--padding", type=positive_vec2_type, metavar=get_vec2_format(), default=None, help="this setting overrides padx and pady.\nsets both horizontal and vertical padding")
    arg_parser.add_argument("-aspect", "--aspect-ratio", type=ratio_type, metavar=get_ratio_format(), help="the desired aspect ratio of the output image.\nfit to text if <= 0 or not specified.\ncalculated from min-size if provided and this setting is not")
    arg_parser.add_argument("-size", "--min-size", type=positive_vec2_type, metavar=get_vec2_format(), help="the minimum size of the image.\nif the text does not fit, the image is expanded")

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
                ligatures=opt.ligatures,
                fill_color=opt.fill_color,
                stroke_width=opt.stroke_width,
                stroke_color=opt.stroke_color,
                multiline_align=opt.multiline_align,
                multiline_spacing=opt.multiline_spacing,
                baseline_align=opt.baseline_align,
                background_color=opt.background_color,
                shadow_color=opt.shadow_color,
                shadow_color_blend=opt.shadow_color_blend,
                shadow_color_blend_method=opt.shadow_color_blend_method,
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
