#!/usr/bin/env python 

import pangocairo
import cairo
import pango
import sys
from gtk import gdk

def usage():
    print "usage: draw_theory_logo.py VERSION OUTPUTFILE"

def set_context_color(c,color):
    col = gdk.color_parse(color)
    r = float(col.red) / 65535
    g = float(col.green) / 65535
    b = float(col.blue) / 65535
    c.set_source_rgb(r,g,b)

def main():
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)

    version = sys.argv[1]
    imgpath = sys.argv[2]

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 140,24)
    ctx = cairo.Context(surface)
    c = pangocairo.CairoContext(ctx)

    l = c.create_layout()
    font_desc = pango.FontDescription('Grixel Acme 7 Wide Bold 14')
    l.set_font_description(font_desc)
    fo = cairo.FontOptions()
    fo.set_antialias(cairo.ANTIALIAS_NONE)

    c.set_font_options(fo)
    pangocairo.context_set_font_options (l.get_context(), fo)
    l.set_text('theory')
    set_context_color(ctx,'#333333')
    ctx.move_to(4,-8)
    c.show_layout(l)
    c.update_layout(l)


    l = c.create_layout()
    font_desc = pango.FontDescription('Grixel Acme 7 Wide 7')
    attr = pango.AttrList()
    attr.insert(pango.AttrLetterSpacing(1200,0,100))
    l.set_attributes(attr)
    l.set_font_description(font_desc)
    fo = cairo.FontOptions()
    fo.set_antialias(cairo.ANTIALIAS_NONE)
    pangocairo.context_set_font_options (l.get_context(), fo)
    l.set_text(version)
    ctx.move_to(105,8)
    ctx.set_source_rgb (.33,.33,.33)

    c.show_layout(l)
    c.update_layout(l)

    surface.write_to_png(imgpath)

if __name__ ==  "__main__":
    main()
