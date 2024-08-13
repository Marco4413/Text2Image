#!/bin/python3

import text2image as t2i
from os import path

if __name__ == "__main__":
    out_dir = path.join(path.dirname(__file__), "test")
    font_path = path.join(path.dirname(__file__), "JetBrainsMono.ttf")
    font = t2i.ImageFont.truetype(font_path, t2i.pt(48))

    t2i.generate_and_save_text_image(
        "Foo\nBar\nBaz",
        out_directory=out_dir,
        font=font,
    )
