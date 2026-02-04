"""
Generate template.pptx — a branded landscape template.

Run once:  python create_template.py
Produces:  assets/template.pptx

The pptx_generator adds all shapes directly to blank slides,
so this template simply sets dimensions and serves as the base file.
"""

from pptx import Presentation
from pptx.util import Inches
import os

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)


def build():
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    os.makedirs("assets", exist_ok=True)
    prs.save("assets/template.pptx")
    print("assets/template.pptx created successfully.")


if __name__ == "__main__":
    build()
