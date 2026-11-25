#!/usr/bin/python3
# Terminal for Raspberry Pi, styled after Windows Terminal (dark).
import os
import sys
import re
import json
import math
import time
import shutil
import signal
import threading
import subprocess

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango, Gio, GObject  # noqa: E402,F401
import cairo  # noqa: E402

HOME = os.path.expanduser("~")
C_ACCENT = "#4CC2FF"
def hexc(h, a=1.0):
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def _rr(cr, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path()


def _line(cr, *pts):
    cr.move_to(*pts[0])
    for p in pts[1:]:
        cr.line_to(*p)
    cr.stroke()


def draw_glyph(cr, name, s, col):
    """Monochrome line icons for buttons."""
    cr.save()
    cr.scale(s / 16.0, s / 16.0)
    cr.set_source_rgba(*col)
    cr.set_line_width(1.15)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    pi = math.pi
    L = lambda *p: _line(cr, *p)  # noqa: E731
    if name == "back":
        L((13.5, 8), (2.5, 8))
        L((7, 3.5), (2.5, 8), (7, 12.5))
    elif name == "forward":
        L((2.5, 8), (13.5, 8))
        L((9, 3.5), (13.5, 8), (9, 12.5))
    elif name == "up":
        L((8, 13.5), (8, 2.5))
        L((3.5, 7), (8, 2.5), (12.5, 7))
    elif name == "refresh":
        cr.arc(8, 8, 5.5, -pi * 0.35, pi * 1.55)
        cr.stroke()
        L((12.9, 1.8), (12.6, 4.9), (9.6, 4.6))
    elif name == "plus":
        L((8, 2.5), (8, 13.5))
        L((2.5, 8), (13.5, 8))
    elif name == "new":
        cr.set_source_rgba(*hexc(C_ACCENT))
        cr.arc(8, 8, 6.5, 0, 2 * pi)
        cr.stroke()
        L((8, 4.8), (8, 11.2))
        L((4.8, 8), (11.2, 8))
    elif name == "cut":
        cr.arc(4.5, 12, 2, 0, 2 * pi)
        cr.stroke()
        cr.arc(11.5, 12, 2, 0, 2 * pi)
        cr.stroke()
        L((5.8, 10.5), (11, 1.8))
        L((10.2, 10.5), (5, 1.8))
    elif name == "copy":
        _rr(cr, 5, 1.5, 9, 10.5, 1.5)
        cr.stroke()
        cr.move_to(3, 4.5)
        cr.line_to(3, 13)
        cr.arc_negative(4.5, 13, 1.5, pi, pi / 2)
        cr.line_to(11, 14.5)
        cr.stroke()
    elif name == "paste":
        _rr(cr, 2.5, 3, 11, 11.5, 1.5)
        cr.stroke()
        _rr(cr, 5.5, 1.5, 5, 3, 1)
        cr.stroke()
        L((5.5, 8), (10.5, 8))
        L((5.5, 11), (9, 11))
    elif name == "rename":
        _rr(cr, 1.5, 4.5, 13, 7, 1.3)
        cr.stroke()
        L((4, 8), (8, 8))
        L((10.5, 2.5), (10.5, 13.5))
        L((9, 2.5), (12, 2.5))
        L((9, 13.5), (12, 13.5))
    elif name == "delete" or name == "trash":
        L((2.5, 4), (13.5, 4))
        L((6, 4), (6.5, 2), (9.5, 2), (10, 4))
        cr.move_to(4, 4)
        cr.line_to(4.8, 14)
        cr.line_to(11.2, 14)
        cr.line_to(12, 4)
        cr.stroke()
        L((6.8, 6.8), (7, 11.5))
        L((9.2, 6.8), (9, 11.5))
    elif name == "sort":
        L((4.5, 2.5), (4.5, 13.5))
        L((2, 5), (4.5, 2.5), (7, 5))
        L((11.5, 2.5), (11.5, 13.5))
        L((9, 11), (11.5, 13.5), (14, 11))
    elif name == "view":
        for y in (3, 8, 13):
            L((2, y), (14, y))
    elif name == "more":
        for x in (3, 8, 13):
            cr.arc(x, 8, 1.1, 0, 2 * pi)
            cr.fill()
    elif name == "chevdown":
        L((4, 6), (8, 10), (12, 6))
    elif name == "chevright":
        L((6, 4), (10, 8), (6, 12))
    elif name == "close":
        L((3.5, 3.5), (12.5, 12.5))
        L((12.5, 3.5), (3.5, 12.5))
    elif name == "min":
        L((3, 8), (13, 8))
    elif name == "max":
        _rr(cr, 3, 3, 10, 10, 1.2)
        cr.stroke()
    elif name == "restore":
        _rr(cr, 3, 5, 8, 8, 1.2)
        cr.stroke()
        L((5, 3), (12, 3), (13, 4), (13, 11))
    elif name == "search":
        cr.arc(6.6, 6.6, 4.6, 0, 2 * pi)
        cr.stroke()
        L((10, 10), (14, 14))
    elif name == "pane":
        _rr(cr, 1.5, 2.5, 13, 11, 1.5)
        cr.stroke()
        L((10, 2.5), (10, 13.5))
    elif name == "terminal":
        _rr(cr, 1.5, 2.5, 13, 11, 1.5)
        cr.stroke()
        L((4, 6), (6.5, 8), (4, 10))
        L((8, 10.5), (11.5, 10.5))
    elif name == "properties":
        _rr(cr, 2.5, 1.5, 11, 13, 1.5)
        cr.stroke()
        for y in (5, 8, 11):
            cr.arc(5.2, y, 0.8, 0, 2 * pi)
            cr.fill()
            L((7.2, y), (11, y))
    elif name == "pin":
        cr.move_to(6, 2)
        cr.line_to(10, 2)
        cr.line_to(9.5, 6.5)
        cr.line_to(12, 9)
        cr.line_to(4, 9)
        cr.line_to(6.5, 6.5)
        cr.close_path()
        cr.stroke()
        L((8, 9), (8, 14))
    elif name == "pin-fill":
        cr.set_line_width(1.0)
        cr.translate(8, 8)
        cr.rotate(pi / 4)
        cr.translate(-8, -8)
        cr.move_to(6, 2)
        cr.line_to(10, 2)
        cr.line_to(9.5, 6.5)
        cr.line_to(12, 9)
        cr.line_to(4, 9)
        cr.line_to(6.5, 6.5)
        cr.close_path()
        cr.stroke()
        L((8, 9), (8, 14))
    elif name == "folder":
        cr.move_to(1.5, 4)
        cr.line_to(6, 4)
        cr.line_to(7.5, 5.5)
        cr.line_to(14.5, 5.5)
        cr.line_to(14.5, 13)
        cr.line_to(1.5, 13)
        cr.close_path()
        cr.stroke()
    elif name == "file":
        cr.move_to(3.5, 1.5)
        cr.line_to(9.5, 1.5)
        cr.line_to(12.5, 4.5)
        cr.line_to(12.5, 14.5)
        cr.line_to(3.5, 14.5)
        cr.close_path()
        cr.stroke()
        L((9.5, 1.5), (9.5, 4.5), (12.5, 4.5))
    elif name == "zip":
        _rr(cr, 2.5, 1.5, 11, 13, 1.5)
        cr.stroke()
        for y in (3, 5, 7):
            L((7, y), (9, y))
        _rr(cr, 6.5, 9, 3, 3.5, 0.6)
        cr.stroke()
    elif name == "extract":
        _rr(cr, 2.5, 6.5, 11, 8, 1.5)
        cr.stroke()
        L((8, 1.5), (8, 10))
        L((5.5, 7.5), (8, 10), (10.5, 7.5))
    elif name == "restoreitem":
        cr.arc(8.5, 8.5, 5, -pi * 0.9, pi * 0.6)
        cr.stroke()
        L((2, 3.5), (3.6, 6.6), (6.6, 5.4))
    elif name == "open":
        _rr(cr, 1.5, 1.5, 13, 13, 2)
        cr.stroke()
        L((7, 9), (12.5, 3.5))
        L((8.5, 3.5), (12.5, 3.5), (12.5, 7.5))
    elif name == "newtab":
        _rr(cr, 1.5, 3.5, 13, 10, 1.5)
        cr.stroke()
        L((1.5, 6), (8, 6))
        L((8, 3.5), (8, 6))
    elif name == "check":
        L((3, 8.5), (6.5, 12), (13, 4.5))
    elif name == "eject":
        cr.move_to(8, 3)
        cr.line_to(13, 9)
        cr.line_to(3, 9)
        cr.close_path()
        cr.stroke()
        L((3, 12.5), (13, 12.5))
    elif name == "details-view":
        for y in (3.5, 8, 12.5):
            _rr(cr, 1.5, y - 1.2, 2.4, 2.4, 0.5)
            cr.stroke()
            L((6, y), (14.5, y))
    elif name == "icons-view":
        for x in (2, 9):
            for y in (2, 9):
                _rr(cr, x, y, 5, 5, 1.2)
                cr.stroke()
    elif name == "selectall":
        _rr(cr, 2, 2, 12, 12, 1.5)
        cr.stroke()
        L((5, 8), (7.2, 10.2), (11, 6))
    elif name == "info":
        cr.arc(8, 8, 6, 0, 2 * pi)
        cr.stroke()
        L((8, 7), (8, 11.5))
        cr.arc(8, 4.8, 0.9, 0, 2 * pi)
        cr.fill()
    elif name == "share":
        cr.arc(4, 8, 1.8, 0, 2 * pi)
        cr.stroke()
        cr.arc(12, 3.8, 1.8, 0, 2 * pi)
        cr.stroke()
        cr.arc(12, 12.2, 1.8, 0, 2 * pi)
        cr.stroke()
        L((5.6, 7.1), (10.4, 4.7))
        L((5.6, 8.9), (10.4, 11.3))
    elif name == "network":
        _rr(cr, 5, 1.5, 6, 4.5, 1)
        cr.stroke()
        L((8, 6), (8, 9))
        L((3, 9), (13, 9))
        L((3, 9), (3, 11))
        L((13, 9), (13, 11))
        _rr(cr, 1, 11, 4, 3.5, 0.8)
        cr.stroke()
        _rr(cr, 11, 11, 4, 3.5, 0.8)
        cr.stroke()
    elif name == "link":
        cr.arc(5.5, 10.5, 3, pi * 0.25, pi * 1.75)
        cr.stroke()
        cr.arc(10.5, 5.5, 3, pi * 1.25, pi * 0.75)
        cr.stroke()
        L((6.5, 9.5), (9.5, 6.5))
    else:
        draw_glyph_extra(cr, name, L, pi)
    cr.restore()




# ----------------------------------------------------------------------------
# Shared Windows 11 dark style
# ----------------------------------------------------------------------------
BASE_CSS = """
* { font-family: "Segoe UI Variable Text", "Segoe UI", "Selawik", "Open Sans", "Noto Sans", sans-serif; }
window.fx, window.fx-dialog { background-color: #202020; color: #ffffff; font-size: 12px; }
.fx label { color: #ffffff; }
headerbar.fx-title { background: #202020; border: none; box-shadow: none; min-height: 40px; padding: 0; margin: 0; }
headerbar.fx-title:backdrop { background: #202020; }
.app-title { font-size: 12px; color: #ffffff; margin-left: 4px; }
.app-title:backdrop { color: rgba(255,255,255,0.55); }
button.wc { background: transparent; border: none; border-radius: 0; min-width: 46px; min-height: 32px; padding: 0; box-shadow: none; }
button.wc:hover { background-color: rgba(255,255,255,0.06); }
button.wc.close:hover { background-color: #C42B1C; }
.tabstrip { margin-top: 6px; margin-left: 6px; }
button.tab { outline-color: transparent; background: transparent; border: none; border-radius: 8px 8px 0 0; min-height: 34px;
   padding: 0 6px 0 12px; box-shadow: none; margin-right: 1px; }
button.tab:hover { background-color: rgba(255,255,255,0.04); }
button.tab.active { background-color: #2C2C2C; }
button.tab label { font-size: 12px; }
button.tab-x { background: transparent; border: none; border-radius: 4px; min-width: 24px; min-height: 24px; padding: 0; box-shadow: none; }
button.tab-x:hover { background-color: rgba(255,255,255,0.08); }
button.tab-new { background: transparent; border: none; border-radius: 4px; min-width: 32px; min-height: 28px; padding: 0;
   box-shadow: none; margin-top: 4px; margin-left: 2px; }
button.tab-new:hover { background-color: rgba(255,255,255,0.06); }
.bar { background-color: #2C2C2C; padding: 4px 8px; }
.bar-bottom { border-bottom: 1px solid rgba(255,255,255,0.06); }
button.tb, button.nb { background: transparent; border: none; border-radius: 4px; min-height: 32px; padding: 0 9px; box-shadow: none; color: #ffffff; }
button.nb { min-width: 34px; padding: 0; }
button.tb:hover, button.nb:hover { background-color: rgba(255,255,255,0.06); }
button.tb:active, button.nb:active { background-color: rgba(255,255,255,0.04); }
button.tb:disabled label { color: rgba(255,255,255,0.36); }
button.tb label { font-size: 12px; }
button.tb.on, button.nb.on { background-color: rgba(255,255,255,0.09); }
.vsep { background-color: rgba(255,255,255,0.08); min-width: 1px; margin: 6px 6px; }
.status { background-color: #202020; padding: 4px 12px; border-top: 1px solid rgba(255,255,255,0.06); }
.status label { font-size: 12px; color: rgba(255,255,255,0.786); }
.sec { color: rgba(255,255,255,0.786); }
.ter { color: rgba(255,255,255,0.545); }
.big-title { font-size: 20px; font-weight: 600; }
.sect-title { font-size: 14px; font-weight: 600; }
entry.field, entry.fx-search { background-color: rgba(255,255,255,0.06); color: #ffffff; border: 1px solid rgba(255,255,255,0.07);
   border-bottom: 1px solid rgba(255,255,255,0.54); border-radius: 4px; min-height: 30px; padding: 0 10px; box-shadow: none;
   font-size: 12px; caret-color: #ffffff; }
entry.field:focus, entry.fx-search:focus { background-color: #1c1c1c; border-bottom: 2px solid #4CC2FF; }
entry selection, textview text selection, entry selection:focus, textview text selection:focus { background-color: #0078D4; color: #ffffff; }
scrollbar { background: transparent; border: none; }
scrollbar slider { background-color: rgba(255,255,255,0.45); border-radius: 6px; min-width: 3px; min-height: 3px; border: none; }
scrollbar:hover slider { min-width: 6px; min-height: 6px; background-color: rgba(255,255,255,0.55); }
scrollbar trough { background: transparent; border: none; }
scale trough { background-color: rgba(255,255,255,0.3); border: none; border-radius: 2px; min-height: 4px; min-width: 4px; }
scale highlight { background-color: #4CC2FF; border: none; border-radius: 2px; min-height: 4px; min-width: 4px; }
scale slider { background-color: #4CC2FF; border: 5px solid #454545; border-radius: 50%; min-width: 12px; min-height: 12px; box-shadow: none; }
scale slider:hover { border-width: 4px; }
menu, .menu, .context-menu { background-color: #2C2C2C; color: #ffffff; border: 1px solid rgba(0,0,0,0.45); border-radius: 8px; padding: 4px; }
menu menuitem { padding: 6px 12px; border-radius: 4px; color: #ffffff; min-height: 18px; }
menu menuitem:hover { background-color: rgba(255,255,255,0.06); }
menu menuitem:disabled label { color: rgba(255,255,255,0.36); }
menu menuitem label { color: #ffffff; font-size: 12px; }
menu menuitem arrow { color: rgba(255,255,255,0.786); }
menu separator { background-color: rgba(255,255,255,0.08); margin: 4px 0; min-height: 1px; }
window.fx button, window.fx-dialog button { background-image: none; text-shadow: none; -gtk-icon-shadow: none; }
button.primary { background-color: #4CC2FF; color: #000000; border: none; border-radius: 4px; min-height: 30px; padding: 0 16px; box-shadow: none; }
button.primary label { color: #000000; }
button.primary:hover { background-color: #48B1E8; }
button.secondary { background-color: rgba(255,255,255,0.06); color: #ffffff; border: 1px solid rgba(255,255,255,0.09); border-radius: 4px; min-height: 30px; padding: 0 16px; box-shadow: none; }
button.secondary:hover { background-color: rgba(255,255,255,0.09); }
.dlg-body { background-color: #2B2B2B; padding: 24px; }
.dlg-foot { background-color: #202020; padding: 22px 24px; border-top: 1px solid rgba(0,0,0,0.3); }
.dlg-title { font-size: 20px; font-weight: 600; }
.fx-dialog label { color: #ffffff; }
.fx-dialog label.sec { color: rgba(255,255,255,0.786); }
.fx-dialog label.ter { color: rgba(255,255,255,0.545); }
checkbutton check { background-color: rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.6); border-radius: 4px; min-width: 18px; min-height: 18px; -gtk-icon-source: none; color: #000000; }
checkbutton check:checked { background-color: #4CC2FF; border-color: #4CC2FF; -gtk-icon-source: -gtk-icontheme("object-select-symbolic"); }
checkbutton label { color: #ffffff; font-size: 12px; margin-left: 6px; }
radiobutton radio { background-color: rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.6); border-radius: 50%; min-width: 18px; min-height: 18px; -gtk-icon-source: none; }
radiobutton radio:checked { background-color: #000000; border: 5px solid #4CC2FF; }
radiobutton label { color: #ffffff; font-size: 12px; margin-left: 6px; }
switch { background-color: transparent; border: 1px solid rgba(255,255,255,0.6); border-radius: 12px; min-width: 40px; min-height: 18px; }
switch:checked { background-color: #4CC2FF; border-color: #4CC2FF; }
switch slider { background-color: rgba(255,255,255,0.8); border-radius: 50%; min-width: 12px; min-height: 12px; margin: 3px; border: none; box-shadow: none; }
switch:checked slider { background-color: #000000; }
switch image { color: transparent; }
combobox button, combobox box { background-color: rgba(255,255,255,0.06); color: #ffffff; border: 1px solid rgba(255,255,255,0.07); border-radius: 4px; box-shadow: none; min-height: 30px; }
combobox button cellview, combobox button label, combobox arrow { color: #ffffff; }
spinbutton { background-color: rgba(255,255,255,0.06); color: #ffffff; border: 1px solid rgba(255,255,255,0.07); border-radius: 4px; box-shadow: none; }
spinbutton entry { background: transparent; border: none; box-shadow: none; color: #ffffff; }
spinbutton button { background: transparent; border: none; box-shadow: none; color: #ffffff; }
tooltip, tooltip.background { background-color: #2C2C2C; border: 1px solid rgba(0,0,0,0.4); border-radius: 4px; }
tooltip label { color: #ffffff; font-size: 12px; }
.set-group { background-color: rgba(255,255,255,0.05); border-radius: 4px; border: 1px solid rgba(0,0,0,0.2); padding: 12px 16px; }
.set-head { font-size: 13px; }
.set-desc { font-size: 12px; color: rgba(255,255,255,0.6); }
"""


def apply_css(extra=""):
    prov = Gtk.CssProvider()
    prov.load_from_data((BASE_CSS + extra).encode())
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 10)
    Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)


def draw_glyph_extra(cr, name, L, pi):
    if name == "save":
        _rr(cr, 2, 2, 12, 12, 1.5)
        cr.stroke()
        _rr(cr, 4.5, 2, 6, 4, 0.5)
        cr.stroke()
        _rr(cr, 4.5, 9, 7, 5, 0.5)
        cr.stroke()
    elif name == "undo":
        cr.move_to(3, 7)
        cr.curve_to(6, 3.5, 13, 4.5, 13, 10)
        cr.stroke()
        L((3, 3), (3, 7), (7, 7))
    elif name == "redo":
        cr.move_to(13, 7)
        cr.curve_to(10, 3.5, 3, 4.5, 3, 10)
        cr.stroke()
        L((13, 3), (13, 7), (9, 7))
    elif name == "replace":
        L((2, 5), (10, 5))
        L((7.5, 2.5), (10, 5), (7.5, 7.5))
        L((14, 11), (6, 11))
        L((8.5, 8.5), (6, 11), (8.5, 13.5))
    elif name == "zoomin":
        cr.arc(6.6, 6.6, 4.6, 0, 2 * pi)
        cr.stroke()
        L((10, 10), (14, 14))
        L((4.6, 6.6), (8.6, 6.6))
        L((6.6, 4.6), (6.6, 8.6))
    elif name == "zoomout":
        cr.arc(6.6, 6.6, 4.6, 0, 2 * pi)
        cr.stroke()
        L((10, 10), (14, 14))
        L((4.6, 6.6), (8.6, 6.6))
    elif name == "fit":
        L((2, 5.5), (2, 2), (5.5, 2))
        L((10.5, 2), (14, 2), (14, 5.5))
        L((14, 10.5), (14, 14), (10.5, 14))
        L((5.5, 14), (2, 14), (2, 10.5))
    elif name == "wrap":
        L((2, 3), (14, 3))
        cr.move_to(2, 8)
        cr.line_to(11.5, 8)
        cr.curve_to(15, 8, 15, 13, 11.5, 13)
        cr.line_to(8, 13)
        cr.stroke()
        L((9.5, 11.3), (8, 13), (9.5, 14.7))
        L((2, 13), (5, 13))
    elif name == "play":
        cr.move_to(4.5, 2.5)
        cr.line_to(13, 8)
        cr.line_to(4.5, 13.5)
        cr.close_path()
        cr.fill()
    elif name == "pause":
        _rr(cr, 3.5, 2.5, 3, 11, 0.8)
        cr.fill()
        _rr(cr, 9.5, 2.5, 3, 11, 0.8)
        cr.fill()
    elif name in ("next", "prev"):
        if name == "prev":
            cr.translate(16, 0)
            cr.scale(-1, 1)
        cr.move_to(3, 3)
        cr.line_to(10.5, 8)
        cr.line_to(3, 13)
        cr.close_path()
        cr.fill()
        _rr(cr, 11, 3, 2, 10, 0.6)
        cr.fill()
    elif name == "shuffle":
        L((2, 4), (5, 4), (11, 12), (14, 12))
        L((2, 12), (5, 12), (11, 4), (14, 4))
        L((12, 2), (14, 4), (12, 6))
        L((12, 10), (14, 12), (12, 14))
    elif name in ("repeat", "repeat1"):
        cr.move_to(3, 9)
        cr.line_to(3, 6)
        cr.arc(5, 6, 2, pi, 1.5 * pi)
        cr.line_to(13, 4)
        cr.stroke()
        L((11, 2), (13, 4), (11, 6))
        cr.move_to(13, 7)
        cr.line_to(13, 10)
        cr.arc(11, 10, 2, 0, 0.5 * pi)
        cr.line_to(3, 12)
        cr.stroke()
        L((5, 10), (3, 12), (5, 14))
        if name == "repeat1":
            cr.set_font_size(5)
            cr.move_to(6.8, 9.8)
            cr.show_text("1")
    elif name in ("volume", "mute"):
        cr.move_to(1.5, 6)
        cr.line_to(4.5, 6)
        cr.line_to(8, 2.5)
        cr.line_to(8, 13.5)
        cr.line_to(4.5, 10)
        cr.line_to(1.5, 10)
        cr.close_path()
        cr.stroke()
        if name == "mute":
            L((10.5, 6), (14.5, 10))
            L((14.5, 6), (10.5, 10))
        else:
            cr.arc(8, 8, 3.5, -pi / 3.5, pi / 3.5)
            cr.stroke()
            cr.arc(8, 8, 6.2, -pi / 3.5, pi / 3.5)
            cr.stroke()
    elif name == "fullscreen":
        L((2, 6), (2, 2), (6, 2))
        L((10, 2), (14, 2), (14, 6))
        L((14, 10), (14, 14), (10, 14))
        L((6, 14), (2, 14), (2, 10))
        L((2, 2), (6, 6))
        L((14, 14), (10, 10))
    elif name == "unfullscreen":
        L((6, 2), (6, 6), (2, 6))
        L((10, 2), (10, 6), (14, 6))
        L((10, 14), (10, 10), (14, 10))
        L((6, 14), (6, 10), (2, 10))
    elif name == "rotate":
        cr.arc(8, 9, 5, pi * 1.15, pi * 2.85)
        cr.stroke()
        L((2.5, 2.5), (3.4, 6.4), (7.2, 5.4))
    elif name == "heart":
        cr.move_to(8, 13.5)
        cr.curve_to(1, 8, 1.5, 2.5, 5, 2.5)
        cr.curve_to(6.5, 2.5, 7.5, 3.5, 8, 4.5)
        cr.curve_to(8.5, 3.5, 9.5, 2.5, 11, 2.5)
        cr.curve_to(14.5, 2.5, 15, 8, 8, 13.5)
        cr.stroke()
    elif name == "pen":
        L((2.5, 13.5), (3.2, 10.5), (11, 2.7), (13.3, 5), (5.5, 12.8), (2.5, 13.5))
        L((9.5, 4.2), (11.8, 6.5))
    elif name == "highlighter":
        L((3, 13.5), (13, 13.5))
        cr.move_to(5, 11)
        cr.line_to(11, 3)
        cr.line_to(13.5, 5)
        cr.line_to(7.5, 12.5)
        cr.line_to(5, 12.5)
        cr.close_path()
        cr.stroke()
    elif name == "eraser":
        cr.move_to(2.5, 10)
        cr.line_to(9, 3.5)
        cr.line_to(13.5, 8)
        cr.line_to(8, 13.5)
        cr.line_to(5.5, 13.5)
        cr.close_path()
        cr.stroke()
        L((6, 6.5), (10.5, 11))
        L((8, 13.5), (14, 13.5))
    elif name == "crop":
        L((4.5, 1.5), (4.5, 11.5), (14.5, 11.5))
        L((1.5, 4.5), (11.5, 4.5), (11.5, 14.5))
    elif name == "camera":
        _rr(cr, 1.5, 4, 13, 9.5, 1.6)
        cr.stroke()
        L((5, 4), (6, 2.5), (10, 2.5), (11, 4))
        cr.arc(8, 8.8, 2.6, 0, 2 * pi)
        cr.stroke()
    elif name == "timer":
        cr.arc(8, 9, 5.5, 0, 2 * pi)
        cr.stroke()
        L((8, 9), (8, 5.8))
        L((6.3, 1.8), (9.7, 1.8))
    elif name == "settings":
        n = 8
        cr.new_path()
        for i in range(n * 2):
            a = i * pi / n
            r = 6.6 if i % 2 == 0 else 5.0
            a1, a2 = a - pi / (n * 2.4), a + pi / (n * 2.4)
            cr.line_to(8 + r * math.cos(a1), 8 + r * math.sin(a1))
            cr.line_to(8 + r * math.cos(a2), 8 + r * math.sin(a2))
        cr.close_path()
        cr.stroke()
        cr.arc(8, 8, 2.2, 0, 2 * pi)
        cr.stroke()
    elif name == "history":
        cr.arc(8, 8, 6, pi * 1.05, pi * 2.85)
        cr.stroke()
        L((1.2, 6.2), (2.3, 8.6), (4.6, 7.3))
        L((8, 4.6), (8, 8.2), (10.5, 9.7))
    elif name == "image":
        _rr(cr, 1.5, 2.5, 13, 11, 1.5)
        cr.stroke()
        L((1.5, 11), (5.5, 7), (9, 10.5), (11, 8.5), (14.5, 12))
        cr.arc(10.5, 5.5, 1.2, 0, 2 * pi)
        cr.stroke()
    elif name == "music":
        cr.arc(4.5, 12, 2, 0, 2 * pi)
        cr.stroke()
        cr.arc(12, 10.5, 2, 0, 2 * pi)
        cr.stroke()
        L((6.5, 12), (6.5, 3.5), (14, 2), (14, 10.5))
    elif name == "video":
        _rr(cr, 1.5, 3.5, 9.5, 9, 1.5)
        cr.stroke()
        L((11, 6.5), (14.5, 4.5), (14.5, 11.5), (11, 9.5))
    elif name == "queue":
        for y in (3, 7):
            L((2, y), (14, y))
        L((2, 11), (8, 11))
        cr.move_to(10.5, 9)
        cr.line_to(14, 11.5)
        cr.line_to(10.5, 14)
        cr.close_path()
        cr.fill()
    elif name == "edit":
        L((2.5, 13.5), (3.2, 10.5), (11, 2.7), (13.3, 5), (5.5, 12.8), (2.5, 13.5))
    elif name == "slideshow":
        _rr(cr, 1.5, 2.5, 13, 9, 1.5)
        cr.stroke()
        cr.move_to(6.5, 5)
        cr.line_to(10, 7)
        cr.line_to(6.5, 9)
        cr.close_path()
        cr.fill()
        L((5, 14), (11, 14))
    elif name == "print":
        _rr(cr, 1.5, 6, 13, 6, 1.2)
        cr.stroke()
        L((4.5, 6), (4.5, 1.5), (11.5, 1.5), (11.5, 6))
        _rr(cr, 4.5, 9.5, 7, 5, 0.5)
        cr.stroke()
    elif name == "wallpaper":
        _rr(cr, 1.5, 2.5, 13, 9, 1.2)
        cr.stroke()
        L((1.5, 9.5), (5, 6), (8, 9), (10, 7), (14.5, 10.5))
        L((5.5, 14), (10.5, 14))
        L((8, 11.5), (8, 14))
    elif name == "list":
        for y in (3.5, 8, 12.5):
            cr.arc(2.5, y, 0.9, 0, 2 * pi)
            cr.fill()
            L((5.5, y), (14, y))
    elif name == "add":
        L((8, 2.5), (8, 13.5))
        L((2.5, 8), (13.5, 8))
    elif name == "split":
        _rr(cr, 1.5, 2.5, 13, 11, 1.5)
        cr.stroke()
        L((8, 2.5), (8, 13.5))
    elif name == "keyboard":
        _rr(cr, 1, 3.5, 14, 9, 1.5)
        cr.stroke()
        for x in (4, 6.7, 9.3, 12):
            cr.rectangle(x - 0.5, 6, 1, 1)
        cr.fill()
        L((4.5, 10), (11.5, 10))


class Icon(Gtk.DrawingArea):
    """Monochrome glyph icon."""

    def __init__(self, name, size=16, color=None):
        super().__init__()
        self.name = name
        self.size = size
        self.color = color
        self.set_size_request(size, size)
        self.set_valign(Gtk.Align.CENTER)
        self.connect("draw", self._draw)

    def set_icon(self, name):
        self.name = name
        self.queue_draw()

    def _draw(self, w, cr):
        col = self.color or (1, 1, 1, 1)
        p = self.get_parent()
        if not self.is_sensitive() or (p and not p.is_sensitive()):
            col = (1, 1, 1, 0.36)
        draw_glyph(cr, self.name, self.size, col)


class WinTitlebar(Gtk.HeaderBar):
    """Title bar with Windows 11 caption buttons. Pack your own widgets with pack_start()."""

    def __init__(self, window):
        super().__init__()
        self.win = window
        self.get_style_context().add_class("fx-title")
        self.set_show_close_button(False)
        self.set_custom_title(Gtk.Box())
        wc = Gtk.Box(spacing=0)
        wc.set_valign(Gtk.Align.START)
        for name, cb, extra in (("min", lambda *_: window.iconify(), ""),
                                ("max", lambda *_: self.toggle_max(), ""),
                                ("close", lambda *_: window.close(), "close")):
            b = Gtk.Button()
            b.get_style_context().add_class("wc")
            if extra:
                b.get_style_context().add_class(extra)
            ic = Icon(name, 10)
            b.add(ic)
            b.connect("clicked", cb)
            if name == "max":
                self.max_icon = ic
            wc.pack_start(b, False, False, 0)
        self.pack_end(wc)
        window.connect("window-state-event", self._wstate)
        window.set_titlebar(self)

    def toggle_max(self):
        if self.win.is_maximized():
            self.win.unmaximize()
        else:
            self.win.maximize()

    def _wstate(self, w, ev):
        maxed = bool(ev.new_window_state & Gdk.WindowState.MAXIMIZED)
        self.max_icon.set_icon("restore" if maxed else "max")
        return False


def app_title(text, logo_draw):
    """Little logo + app name for the left of the title bar."""
    box = Gtk.Box(spacing=8)
    box.set_margin_start(14)
    da = Gtk.DrawingArea()
    da.set_size_request(16, 16)
    da.set_valign(Gtk.Align.CENTER)
    da.connect("draw", lambda w, cr: logo_draw(cr, 16))
    box.pack_start(da, False, False, 0)
    lb = Gtk.Label(label=text)
    lb.get_style_context().add_class("app-title")
    box.pack_start(lb, False, False, 0)
    return box, lb


class JsonSettings(dict):
    def __init__(self, app_dir, defaults):
        super().__init__(defaults)
        self.dir = os.path.join(HOME, ".config", app_dir)
        self.file = os.path.join(self.dir, "settings.json")
        try:
            with open(self.file) as f:
                self.update(json.load(f))
        except (OSError, ValueError):
            pass

    def save(self):
        try:
            os.makedirs(self.dir, exist_ok=True)
            tmp = self.file + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self, f, indent=1)
            os.replace(tmp, self.file)
        except OSError:
            pass


def vsep():
    s = Gtk.Box()
    s.get_style_context().add_class("vsep")
    return s


def logo_pixbuf(draw, size):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    draw(cairo.Context(surf), size)
    return Gdk.pixbuf_get_from_surface(surf, 0, 0, size, size)
def label(text="", cls=None, xalign=0.0, ellipsize=False, wrap=False, markup=False):
    lb = Gtk.Label()
    if markup:
        lb.set_markup(text)
    else:
        lb.set_text(text)
    lb.set_xalign(xalign)
    if cls:
        for c in cls.split():
            lb.get_style_context().add_class(c)
    if ellipsize:
        lb.set_ellipsize(Pango.EllipsizeMode.END)
    if wrap:
        lb.set_line_wrap(True)
        lb.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    return lb


def add_cls(w, *cls):
    ctx = w.get_style_context()
    for c in cls:
        ctx.add_class(c)
    return w


def tb_button(icon, text, cb=None, chev=False, tip=None):
    b = Gtk.Button()
    add_cls(b, "tb")
    box = Gtk.Box(spacing=7)
    if icon:
        box.pack_start(Icon(icon), False, False, 0)
    if text:
        box.pack_start(Gtk.Label(label=text), False, False, 0)
    if chev:
        box.pack_start(Icon("chevdown", 10), False, False, 0)
    b.add(box)
    b.set_relief(Gtk.ReliefStyle.NONE)
    b.set_tooltip_text(tip or text or None)
    if cb:
        b.connect("clicked", lambda w: cb(w))
    return b


def icon_button(icon, cb, cls="nb", tip=None, size=16):
    b = Gtk.Button()
    add_cls(b, cls)
    b.add(Icon(icon, size))
    b.set_relief(Gtk.ReliefStyle.NONE)
    if tip:
        b.set_tooltip_text(tip)
    b.connect("clicked", lambda w: cb(w))
    return b


def build_menu(spec):
    """spec: list of None (separator) or dicts: label, cb, icon, place, accel, sensitive, checked, sub."""
    menu = Gtk.Menu()
    add_cls(menu, "context-menu")
    for it in spec:
        if it is None:
            menu.append(Gtk.SeparatorMenuItem())
            continue
        mi = Gtk.MenuItem()
        box = Gtk.Box(spacing=12)
        ic = None
        if it.get("checked"):
            ic = Icon("check", 16)
        elif it.get("pixbuf") is not None:
            ic = Gtk.Image.new_from_pixbuf(it["pixbuf"])
        elif it.get("icon"):
            ic = Icon(it["icon"], 16)
        if ic is None:
            ic = Gtk.Box()
            ic.set_size_request(16, 16)
        box.pack_start(ic, False, False, 0)
        lb = Gtk.Label(label=it["label"])
        lb.set_xalign(0)
        box.pack_start(lb, True, True, 0)
        if it.get("accel"):
            al = Gtk.Label(label=it["accel"])
            al.get_style_context().add_class("dim-label")
            al.set_opacity(0.55)
            al.set_margin_start(24)
            box.pack_end(al, False, False, 0)
        mi.add(box)
        mi.set_sensitive(it.get("sensitive", True))
        if it.get("sub") is not None:
            mi.set_submenu(build_menu(it["sub"]))
        elif it.get("cb"):
            cb = it["cb"]
            mi.connect("activate", lambda w, cb=cb: GLib.idle_add(cb))
        menu.append(mi)
    menu.show_all()
    return menu


def popup_menu(menu, widget, event=None):
    menu.attach_to_widget(widget, None)
    if event is not None:
        menu.popup_at_pointer(event)
    else:
        menu.popup_at_widget(widget, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None)


# ----------------------------------------------------------------------------
# Windows 11 style dialogs
# ----------------------------------------------------------------------------
class WinDialog(Gtk.Window):
    def __init__(self, parent, title, body=None, primary="OK", secondary="Cancel", width=440, extra=None,
                 markup=False):
        super().__init__(transient_for=parent, modal=True)
        add_cls(self, "fx-dialog")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(width, -1)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_title(title)
        self.cb = None
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        add_cls(self.body, "dlg-body")
        self.body.pack_start(label(title, "dlg-title"), False, False, 0)
        if body:
            lb = label(body, wrap=True, markup=markup)
            lb.set_max_width_chars(60)
            self.body.pack_start(lb, False, False, 0)
        if extra:
            self.body.pack_start(extra, False, False, 0)
        outer.pack_start(self.body, True, True, 0)
        self.foot = Gtk.Box(spacing=8, homogeneous=True)
        add_cls(self.foot, "dlg-foot")
        self.primary_btn = None
        if primary:
            pb = Gtk.Button(label=primary)
            add_cls(pb, "primary")
            pb.connect("clicked", lambda *_: self.done(True))
            self.foot.pack_start(pb, True, True, 0)
            pb.set_can_default(True)
            self.set_default(pb)
            self.primary_btn = pb
        if secondary:
            sb = Gtk.Button(label=secondary)
            add_cls(sb, "secondary")
            sb.connect("clicked", lambda *_: self.done(False))
            self.foot.pack_start(sb, True, True, 0)
        if primary or secondary:
            outer.pack_start(self.foot, False, False, 0)
        self.add(outer)
        self.connect("key-press-event", self._key)

    def _key(self, w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            self.done(False)
            return True
        return False

    def done(self, ok):
        cb = self.cb
        self.cb = None
        self.hide()
        if cb:
            cb(ok)
        self.destroy()

    def ask(self, cb=None):
        self.cb = cb
        self.show_all()
        if self.primary_btn:
            self.primary_btn.grab_focus()


def info_dialog(parent, title, body):
    WinDialog(parent, title, body, primary="OK", secondary=None).ask()


def confirm(parent, title, body, yes, cb, no="Cancel"):
    WinDialog(parent, title, body, primary=yes, secondary=no).ask(cb)


def error_list_dialog(parent, title, errors):
    lines = []
    for p, msg in errors[:12]:
        lines.append(f"{os.path.basename(p) or p}: {msg}" if p else msg)
    if len(errors) > 12:
        lines.append(f"...and {len(errors) - 12} more")
    info_dialog(parent, title, "\n".join(lines))




# ----------------------------------------------------------------------------
# Terminal
# ----------------------------------------------------------------------------
gi.require_version("Vte", "2.91")
from gi.repository import Vte  # noqa: E402

APP_ID = "io.github.piterminal"
DEFAULTS = {"width": 980, "height": 620, "maximized": False, "font": "DejaVu Sans Mono 11", "scheme": "Campbell",
            "cursor": "bar", "blink": True, "scrollback": 10000, "zoom": 1.0, "default_profile": "Bash",
            "confirm_close": True, "bell": False}

SCHEMES = {
    "Campbell": dict(bg="#0C0C0C", fg="#CCCCCC", cursor="#FFFFFF", pal=[
        "#0C0C0C", "#C50F1F", "#13A10E", "#C19C00", "#0037DA", "#881798", "#3A96DD", "#CCCCCC",
        "#767676", "#E74856", "#16C60C", "#F9F1A5", "#3B78FF", "#B4009E", "#61D6D6", "#F2F2F2"]),
    "One Half Dark": dict(bg="#282C34", fg="#DCDFE4", cursor="#FFFFFF", pal=[
        "#282C34", "#E06C75", "#98C379", "#E5C07B", "#61AFEF", "#C678DD", "#56B6C2", "#DCDFE4",
        "#5A6374", "#E06C75", "#98C379", "#E5C07B", "#61AFEF", "#C678DD", "#56B6C2", "#DCDFE4"]),
    "Tango Dark": dict(bg="#000000", fg="#D3D7CF", cursor="#FFFFFF", pal=[
        "#000000", "#CC0000", "#4E9A06", "#C4A000", "#3465A4", "#75507B", "#06989A", "#D3D7CF",
        "#555753", "#EF2929", "#8AE234", "#FCE94F", "#729FCF", "#AD7FA8", "#34E2E2", "#EEEEEC"]),
    "Solarized Dark": dict(bg="#002B36", fg="#839496", cursor="#FFFFFF", pal=[
        "#002B36", "#DC322F", "#859900", "#B58900", "#268BD2", "#D33682", "#2AA198", "#EEE8D5",
        "#073642", "#CB4B16", "#586E75", "#657B83", "#839496", "#6C71C4", "#93A1A1", "#FDF6E3"]),
    "Vintage": dict(bg="#000000", fg="#C0C0C0", cursor="#FFFFFF", pal=[
        "#000000", "#800000", "#008000", "#808000", "#000080", "#800080", "#008080", "#C0C0C0",
        "#808080", "#FF0000", "#00FF00", "#FFFF00", "#0000FF", "#FF00FF", "#00FFFF", "#FFFFFF"]),
    "Raspberry": dict(bg="#1A1014", fg="#E8DDE1", cursor="#F2508C", pal=[
        "#1A1014", "#E8466E", "#7BC86C", "#F2C14E", "#4C8DDB", "#C2507F", "#4FC1C9", "#E8DDE1",
        "#5C4650", "#FF6B8F", "#9BE08D", "#FFD877", "#76A9EB", "#E07AA3", "#7AD9DF", "#FFFFFF"]),
}

PROFILES = [
    ("Bash", None, "terminal"),
    ("Python 3", ["python3"], "python"),
    ("Root shell", ["sudo", "-i"], "shield"),
    ("Raspberry Pi config", ["sudo", "raspi-config"], "settings"),
]

CSS = """
vte-terminal { padding: 6px 4px 2px 10px; }
.findbar { background-color: #2C2C2C; border: 1px solid rgba(0,0,0,0.35); border-radius: 0 0 8px 8px; padding: 6px; }
"""


def draw_logo(cr, s):
    cr.save()
    cr.scale(s / 16.0, s / 16.0)
    cr.set_source_rgba(*hexc("#2B2B2B"))
    _rr(cr, 1, 2, 14, 12, 2.2)
    cr.fill()
    cr.set_source_rgba(*hexc("#4CC2FF"))
    _rr(cr, 1, 2, 14, 2.6, 1.2)
    cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.95)
    cr.set_line_width(1.2)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.move_to(4, 7)
    cr.line_to(6.5, 9)
    cr.line_to(4, 11)
    cr.stroke()
    cr.move_to(8, 11.2)
    cr.line_to(12, 11.2)
    cr.stroke()
    cr.restore()


_orig_extra = draw_glyph_extra


def draw_glyph_extra(cr, name, L, pi):  # noqa: F811
    if name == "python":
        _rr(cr, 2, 2, 12, 12, 3)
        cr.stroke()
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(7)
        cr.move_to(4.1, 10.6)
        cr.show_text("Py")
    elif name == "down":
        L((8, 2.5), (8, 13.5))
        L((3.5, 9), (8, 13.5), (12.5, 9))
    elif name == "shield":
        cr.move_to(8, 1.5)
        cr.line_to(13.5, 3.5)
        cr.curve_to(13.5, 9, 11, 12.5, 8, 14.5)
        cr.curve_to(5, 12.5, 2.5, 9, 2.5, 3.5)
        cr.close_path()
        cr.stroke()
    else:
        _orig_extra(cr, name, L, pi)


def rgba(h):
    c = Gdk.RGBA()
    c.parse(h)
    return c


class Term(Gtk.Box):
    """One tab: a VTE terminal running a shell or program."""

    def __init__(self, win, profile, cwd=None):
        super().__init__()
        self.win = win
        self.profile = profile
        self.pid = None
        self.title = profile[0]
        self.term = Vte.Terminal()
        self.term.set_scrollback_lines(int(win.st["scrollback"]))
        self.term.set_mouse_autohide(True)
        try:
            self.term.set_bold_is_bright(True)
        except AttributeError:
            pass
        sb = Gtk.Scrollbar(orientation=Gtk.Orientation.VERTICAL, adjustment=self.term.get_vadjustment())
        self.pack_start(self.term, True, True, 0)
        self.pack_start(sb, False, False, 0)
        self.apply_prefs()
        self.term.connect("child-exited", self._exited)
        self.term.connect("button-press-event", self._press)
        self.term.connect("scroll-event", self._scroll)
        for sig in ("window-title-changed", "current-directory-uri-changed"):
            try:
                self.term.connect(sig, lambda *a: self._title_changed())
            except TypeError:
                pass
        argv = profile[1] or [os.environ.get("SHELL") or "/bin/bash"]
        env = [f"{k}={v}" for k, v in os.environ.items() if k not in ("COLUMNS", "LINES")]
        env.append("TERM=xterm-256color")
        env.append("COLORTERM=truecolor")
        env.append("TERM_PROGRAM=pi-terminal")
        self.term.spawn_async(Vte.PtyFlags.DEFAULT, cwd or HOME, argv, env, GLib.SpawnFlags.SEARCH_PATH,
                              None, None, -1, None, self._spawned, None)
        self.show_all()

    def _spawned(self, term, pid, err, *a):
        if err is not None or pid == -1:
            msg = getattr(err, "message", str(err))
            self.term.feed(f"\r\nCouldn't start {self.profile[0]}: {msg}\r\n".encode())
            return
        self.pid = pid

    def apply_prefs(self):
        st = self.win.st
        sc = SCHEMES.get(st["scheme"], SCHEMES["Campbell"])
        self.term.set_colors(rgba(sc["fg"]), rgba(sc["bg"]), [rgba(c) for c in sc["pal"]])
        self.term.set_color_cursor(rgba(sc["cursor"]))
        self.term.set_color_cursor_foreground(rgba(sc["bg"]))
        self.term.set_font(Pango.FontDescription.from_string(st["font"]))
        self.term.set_font_scale(st["zoom"])
        self.term.set_cursor_shape({"bar": Vte.CursorShape.IBEAM, "block": Vte.CursorShape.BLOCK,
                                    "underscore": Vte.CursorShape.UNDERLINE}[st["cursor"]])
        self.term.set_cursor_blink_mode(Vte.CursorBlinkMode.ON if st["blink"] else Vte.CursorBlinkMode.OFF)
        self.term.set_audible_bell(bool(st["bell"]))

    def cwd(self):
        if self.pid:
            try:
                return os.readlink(f"/proc/{self.pid}/cwd")
            except OSError:
                pass
        return HOME

    def busy(self):
        """True if a program other than the shell is running in this tab."""
        if not self.pid:
            return False
        try:
            with open(f"/proc/{self.pid}/stat") as f:
                fields = f.read().rsplit(")", 1)[1].split()
            tpgid = int(fields[5])
            return tpgid not in (-1, self.pid) and self.profile[1] is None
        except (OSError, ValueError, IndexError):
            return False

    def _title_changed(self):
        t = None
        try:
            t = self.term.get_window_title()
        except Exception:
            t = None
        if not t:
            c = self.cwd()
            t = "~" + c[len(HOME):] if c.startswith(HOME) else c
        self.title = t
        self.win.tab_title(self)

    def _exited(self, term, status):
        self.win.close_term(self, force=True)

    def _scroll(self, w, ev):
        if ev.state & Gdk.ModifierType.CONTROL_MASK:
            dy = ev.delta_y if ev.direction == Gdk.ScrollDirection.SMOOTH else (
                -1 if ev.direction == Gdk.ScrollDirection.UP else 1)
            if dy:
                self.win.zoom(0.1 if dy < 0 else -0.1)
            return True
        return False

    def _press(self, w, ev):
        if ev.type == Gdk.EventType.BUTTON_PRESS and ev.button == 3:
            self.win.term_menu(self, ev)
            return True
        return False


class TabButton(Gtk.Button):
    def __init__(self, win, t):
        super().__init__()
        self.win = win
        self.t = t
        self.get_style_context().add_class("tab")
        self.set_relief(Gtk.ReliefStyle.NONE)
        box = Gtk.Box(spacing=8)
        box.pack_start(Icon(t.profile[2], 14), False, False, 0)
        self.lbl = label(t.title, ellipsize=True)
        self.lbl.set_width_chars(14)
        self.lbl.set_max_width_chars(24)
        box.pack_start(self.lbl, True, True, 0)
        x = Gtk.Button()
        x.get_style_context().add_class("tab-x")
        x.add(Icon("close", 10))
        x.set_relief(Gtk.ReliefStyle.NONE)
        x.connect("clicked", lambda *_: win.close_term(t))
        box.pack_start(x, False, False, 0)
        self.add(box)
        self.connect("clicked", lambda *_: win.switch(t))
        self.connect("button-press-event", self._press)

    def _press(self, w, ev):
        if ev.button == 2:
            self.win.close_term(self.t)
            return True
        if ev.button == 3:
            m = build_menu([
                {"label": "Duplicate tab", "icon": "newtab", "accel": "Ctrl+Shift+D",
                 "cb": lambda: self.win.new_term(self.t.profile, self.t.cwd())},
                {"label": "Rename tab", "icon": "rename", "cb": lambda: self.win.rename_tab(self.t)},
                None,
                {"label": "Close tab", "icon": "close", "accel": "Ctrl+Shift+W", "cb": lambda: self.win.close_term(self.t)},
                {"label": "Close other tabs", "sensitive": len(self.win.terms) > 1,
                 "cb": lambda: self.win.close_others(self.t)},
            ])
            self.win._menu = m
            popup_menu(m, self, ev)
            return True
        return False

    def set_active(self, on):
        ctx = self.get_style_context()
        (ctx.add_class if on else ctx.remove_class)("active")


class TermWindow(Gtk.ApplicationWindow):
    def __init__(self, app, profile=None, cwd=None):
        super().__init__(application=app)
        self.app = app
        self.st = app.settings
        self.terms = []
        self.tabs = {}
        self.cur = None
        self._menu = None
        self.set_title("Terminal")
        self.set_icon_name("pi-terminal")
        self.get_style_context().add_class("fx")
        self.set_default_size(self.st["width"], self.st["height"])
        if self.st.get("maximized"):
            self.maximize()
        self.connect("delete-event", self._on_close)
        self.connect("key-press-event", self._key)
        self.connect("configure-event", self._configure)
        tb = WinTitlebar(self)
        strip = Gtk.Box()
        strip.get_style_context().add_class("tabstrip")
        strip.set_valign(Gtk.Align.END)
        self.tabbox = Gtk.Box()
        strip.pack_start(self.tabbox, False, False, 0)
        nt = icon_button("plus", lambda w: self.new_term(), cls="tab-new", tip="New tab (Ctrl+Shift+T)", size=14)
        nt.set_valign(Gtk.Align.CENTER)
        strip.pack_start(nt, False, False, 0)
        dd = icon_button("chevdown", self._profiles_menu, cls="tab-new", tip="Open a new tab with a profile", size=12)
        dd.set_valign(Gtk.Align.CENTER)
        strip.pack_start(dd, False, False, 0)
        tb.pack_start(strip)
        tb.show_all()
        ov = Gtk.Overlay()
        self.stack = Gtk.Stack()
        ov.add(self.stack)
        self.findbar = self._build_find()
        ov.add_overlay(self.findbar)
        self.add(ov)
        ov.show_all()
        self.findbar.hide()
        self.new_term(profile, cwd)

    # ---------------- tabs
    def profile_by_name(self, name):
        for p in PROFILES:
            if p[0] == name:
                return p
        return PROFILES[0]

    def new_term(self, profile=None, cwd=None):
        profile = profile or self.profile_by_name(self.st.get("default_profile", "Bash"))
        if cwd is None and self.cur is not None:
            cwd = self.cur.cwd()
        t = Term(self, profile, cwd)
        self.terms.append(t)
        self.stack.add(t)
        tb = TabButton(self, t)
        self.tabs[t] = tb
        self.tabbox.pack_start(tb, False, False, 0)
        tb.show_all()
        self.switch(t)
        return t

    def switch(self, t):
        self.cur = t
        self.stack.set_visible_child(t)
        for tt, tb in self.tabs.items():
            tb.set_active(tt is t)
        self.set_title(t.title)
        t.term.grab_focus()

    def tab_title(self, t):
        tb = self.tabs.get(t)
        if tb and not getattr(t, "fixed_title", None):
            tb.lbl.set_text(t.title)
            tb.set_tooltip_text(t.title)
        if t is self.cur:
            self.set_title(getattr(t, "fixed_title", None) or t.title)

    def rename_tab(self, t):
        ent = Gtk.Entry()
        ent.get_style_context().add_class("field")
        ent.set_text(self.tabs[t].lbl.get_text())
        ent.set_activates_default(True)
        dlg = WinDialog(self, "Rename tab", None, primary="Rename", extra=ent, width=360)

        def done(ok):
            if ok:
                t.fixed_title = ent.get_text().strip() or None
                self.tabs[t].lbl.set_text(t.fixed_title or t.title)
        dlg.ask(done)
        ent.grab_focus()

    def close_term(self, t, force=False):
        if t not in self.terms:
            return

        def really():
            if t not in self.terms:
                return
            i = self.terms.index(t)
            self.terms.remove(t)
            self.tabs.pop(t).destroy()
            if t.pid:
                try:
                    os.kill(t.pid, signal.SIGHUP)
                except OSError:
                    pass
            t.destroy()
            if not self.terms:
                self.destroy()
            elif self.cur is t:
                self.switch(self.terms[max(0, i - 1)])
        if not force and t.busy():
            confirm(self, "Close tab?", "A program is still running in this tab. Close it anyway?", "Close",
                    lambda ok: ok and really())
        else:
            really()

    def close_others(self, keep):
        for t in list(self.terms):
            if t is not keep:
                self.close_term(t, force=True)

    def cycle(self, d):
        i = self.terms.index(self.cur)
        self.switch(self.terms[(i + d) % len(self.terms)])

    # ---------------- menus
    def _profiles_menu(self, w):
        spec = [{"label": p[0], "icon": p[2], "accel": f"Ctrl+Shift+{i + 1}",
                 "cb": (lambda p=p: self.new_term(p))} for i, p in enumerate(PROFILES)]
        spec += [None, {"label": "Settings", "icon": "settings", "accel": "Ctrl+,", "cb": self.settings_dialog},
                 {"label": "About", "icon": "info", "cb": lambda: info_dialog(
                     self, "Terminal", "Terminal for Raspberry Pi (pi-terminal).\nA Windows Terminal style app.")}]
        m = build_menu(spec)
        self._menu = m
        popup_menu(m, w)

    def term_menu(self, t, ev):
        has = t.term.get_has_selection()
        m = build_menu([
            {"label": "Copy", "icon": "copy", "accel": "Ctrl+Shift+C", "sensitive": has, "cb": self.copy},
            {"label": "Paste", "icon": "paste", "accel": "Ctrl+Shift+V", "cb": self.paste},
            {"label": "Select all", "accel": "Ctrl+Shift+A", "cb": lambda: t.term.select_all()},
            {"label": "Find", "icon": "search", "accel": "Ctrl+Shift+F", "cb": self.show_find},
            None,
            {"label": "Open folder in File Explorer", "icon": "open", "cb": lambda: self.open_folder(t)},
            {"label": "New tab", "icon": "plus", "accel": "Ctrl+Shift+T", "cb": lambda: self.new_term()},
            {"label": "Settings", "icon": "settings", "accel": "Ctrl+,", "cb": self.settings_dialog},
        ])
        self._menu = m
        popup_menu(m, t.term, ev)

    def open_folder(self, t):
        cwd = t.cwd()
        try:
            Gio.AppInfo.launch_default_for_uri(Gio.File.new_for_path(cwd).get_uri(), None)
        except GLib.Error:
            pass

    # ---------------- clipboard
    def copy(self):
        if self.cur.term.get_has_selection():
            self.cur.term.copy_clipboard_format(Vte.Format.TEXT)

    def paste(self):
        self.cur.term.paste_clipboard()

    # ---------------- find
    def _build_find(self):
        box = Gtk.Box(spacing=4)
        box.get_style_context().add_class("findbar")
        box.set_halign(Gtk.Align.END)
        box.set_valign(Gtk.Align.START)
        box.set_margin_end(30)
        self.find_entry = Gtk.Entry()
        self.find_entry.get_style_context().add_class("field")
        self.find_entry.set_placeholder_text("Find")
        self.find_entry.set_width_chars(24)
        self.find_entry.connect("changed", lambda *a: self._set_regex())
        self.find_entry.connect("activate", lambda *a: self.find(False))
        box.pack_start(self.find_entry, False, False, 0)
        box.pack_start(icon_button("up", lambda w: self.find(True), tip="Find previous"), False, False, 0)
        box.pack_start(icon_button("down", lambda w: self.find(False), tip="Find next"), False, False, 0)
        box.pack_start(icon_button("close", lambda w: self.hide_find(), tip="Close (Esc)"), False, False, 0)
        return box

    def show_find(self):
        self.findbar.show_all()
        self.find_entry.grab_focus()
        self.find_entry.select_region(0, -1)

    def hide_find(self):
        self.findbar.hide()
        for t in self.terms:
            t.term.search_set_regex(None, 0)
        self.cur.term.grab_focus()

    def _set_regex(self):
        txt = self.find_entry.get_text()
        if not txt:
            self.cur.term.search_set_regex(None, 0)
            return
        try:
            rx = Vte.Regex.new_for_search(re.escape(txt), -1, 0x00000008)  # PCRE2_CASELESS
            self.cur.term.search_set_regex(rx, 0)
            self.cur.term.search_set_wrap_around(True)
        except GLib.Error:
            pass

    def find(self, backward):
        self._set_regex()
        if backward:
            self.cur.term.search_find_previous()
        else:
            self.cur.term.search_find_next()

    # ---------------- prefs
    def zoom(self, d=None, reset=False):
        z = 1.0 if reset else max(0.5, min(3.0, round(self.st["zoom"] + d, 2)))
        self.st["zoom"] = z
        self.app.apply_all()

    def settings_dialog(self):
        st = self.st
        g = Gtk.Grid(column_spacing=16, row_spacing=12)
        r = 0

        def row(text, w):
            nonlocal r
            g.attach(label(text, "sec"), 0, r, 1, 1)
            w.set_hexpand(True)
            g.attach(w, 1, r, 1, 1)
            r += 1
        prof = Gtk.ComboBoxText()
        for p in PROFILES:
            prof.append(p[0], p[0])
        prof.set_active_id(st["default_profile"])
        row("Default profile", prof)
        sch = Gtk.ComboBoxText()
        for n in SCHEMES:
            sch.append(n, n)
        sch.set_active_id(st["scheme"])
        row("Color scheme", sch)
        fb = Gtk.FontButton()
        fb.set_font(st["font"])
        fb.set_filter_func(lambda fam, face, *a: fam.is_monospace(), None)
        row("Font", fb)
        cur = Gtk.ComboBoxText()
        for k, n in (("bar", "Bar ( ┃ )"), ("block", "Filled box ( █ )"), ("underscore", "Underscore ( _ )")):
            cur.append(k, n)
        cur.set_active_id(st["cursor"])
        row("Cursor shape", cur)
        blink = Gtk.Switch()
        blink.set_active(st["blink"])
        blink.set_halign(Gtk.Align.START)
        row("Blinking cursor", blink)
        sb = Gtk.SpinButton.new_with_range(1000, 200000, 1000)
        sb.set_value(st["scrollback"])
        row("History size (lines)", sb)
        bell = Gtk.Switch()
        bell.set_active(st["bell"])
        bell.set_halign(Gtk.Align.START)
        row("Bell sound", bell)
        conf = Gtk.Switch()
        conf.set_active(st["confirm_close"])
        conf.set_halign(Gtk.Align.START)
        row("Warn when closing several tabs", conf)
        dlg = WinDialog(self, "Settings", None, primary="Save", extra=g, width=520)

        def done(ok):
            if not ok:
                return
            st["default_profile"] = prof.get_active_id()
            st["scheme"] = sch.get_active_id()
            st["font"] = fb.get_font()
            st["cursor"] = cur.get_active_id()
            st["blink"] = blink.get_active()
            st["scrollback"] = int(sb.get_value())
            st["bell"] = bell.get_active()
            st["confirm_close"] = conf.get_active()
            st.save()
            self.app.apply_all()
        dlg.ask(done)

    # ---------------- window
    def _configure(self, w, ev):
        if not self.is_maximized():
            self.st["width"], self.st["height"] = self.get_size()
        return False

    def _on_close(self, *a):
        self.st["maximized"] = self.is_maximized()
        self.st.save()
        if len(self.terms) > 1 and self.st.get("confirm_close", True):
            def go(ok):
                if ok:
                    for t in list(self.terms):
                        self.close_term(t, force=True)
            confirm(self, "Close all tabs?", f"You're about to close {len(self.terms)} tabs.", "Close all", go)
            return True
        for t in self.terms:
            if t.pid:
                try:
                    os.kill(t.pid, signal.SIGHUP)
                except OSError:
                    pass
        return False

    def _key(self, w, ev):
        k = Gdk.keyval_to_lower(ev.keyval)
        ctrl = bool(ev.state & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(ev.state & Gdk.ModifierType.SHIFT_MASK)
        if isinstance(self.get_focus(), Gtk.Entry):
            if ev.keyval == Gdk.KEY_Escape:
                self.hide_find()
                return True
            return False
        t = self.cur
        if ctrl and shift and k == Gdk.KEY_t:
            self.new_term()
        elif ctrl and shift and k == Gdk.KEY_w:
            self.close_term(t)
        elif ctrl and shift and k == Gdk.KEY_d:
            self.new_term(t.profile, t.cwd())
        elif ctrl and shift and k == Gdk.KEY_n:
            self.app.new_window(cwd=t.cwd())
        elif ctrl and shift and k == Gdk.KEY_c:
            self.copy()
        elif ctrl and shift and k == Gdk.KEY_v:
            self.paste()
        elif ctrl and shift and k == Gdk.KEY_a:
            t.term.select_all()
        elif ctrl and shift and k == Gdk.KEY_f:
            self.show_find()
        elif ctrl and k == Gdk.KEY_c and not shift and t.term.get_has_selection():
            self.copy()
            t.term.unselect_all()
        elif ctrl and k == Gdk.KEY_v and not shift:
            self.paste()
        elif ctrl and k in (Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab):
            self.cycle(-1 if shift else 1)
        elif ctrl and shift and Gdk.KEY_1 <= ev.keyval <= Gdk.KEY_4:
            self.new_term(PROFILES[ev.keyval - Gdk.KEY_1])
        elif ctrl and shift and ev.keyval in (Gdk.KEY_exclam, Gdk.KEY_at, Gdk.KEY_numbersign, Gdk.KEY_dollar):
            self.new_term(PROFILES[[Gdk.KEY_exclam, Gdk.KEY_at, Gdk.KEY_numbersign, Gdk.KEY_dollar].index(ev.keyval)])
        elif ctrl and k == Gdk.KEY_comma:
            self.settings_dialog()
        elif ctrl and k in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
            self.zoom(0.1)
        elif ctrl and k in (Gdk.KEY_minus, Gdk.KEY_KP_Subtract):
            self.zoom(-0.1)
        elif ctrl and k in (Gdk.KEY_0, Gdk.KEY_KP_0):
            self.zoom(reset=True)
        elif ev.keyval == Gdk.KEY_F11:
            if self.get_window() and self.get_window().get_state() & Gdk.WindowState.FULLSCREEN:
                self.unfullscreen()
            else:
                self.fullscreen()
        elif ev.keyval == Gdk.KEY_Escape and self.findbar.get_visible():
            self.hide_find()
        else:
            return False
        return True


class TermApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.settings = JsonSettings("pi-terminal", DEFAULTS)
        apply_css(CSS)
        self.scheme_css()

    def new_window(self, profile=None, cwd=None):
        w = TermWindow(self, profile, cwd)
        w.present()
        return w

    def scheme_css(self):
        bg = SCHEMES.get(self.settings["scheme"], SCHEMES["Campbell"])["bg"]
        if not hasattr(self, "scheme_prov"):
            self.scheme_prov = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.scheme_prov,
                                                     Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 20)
        self.scheme_prov.load_from_data(f"button.tab.active {{ background-color: {bg}; }}".encode())

    def apply_all(self):
        self.scheme_css()
        for w in self.get_windows():
            if isinstance(w, TermWindow):
                for t in w.terms:
                    t.apply_prefs()

    def do_command_line(self, cmd):
        args = cmd.get_arguments()[1:]
        cwd = cmd.get_cwd() or HOME
        profile = None
        i = 0
        while i < len(args):
            a = args[i]
            if a in ("-d", "--working-directory") and i + 1 < len(args):
                cwd = args[i + 1]
                i += 2
                continue
            if a.startswith("--working-directory="):
                cwd = a.split("=", 1)[1]
            elif a in ("-e", "-x", "--") and i + 1 < len(args):
                rest = args[i + 1:]
                if len(rest) == 1 and " " in rest[0]:
                    rest = ["bash", "-c", rest[0]]
                profile = (os.path.basename(rest[0]), rest, "terminal")
                break
            i += 1
        self.new_window(profile, os.path.expanduser(cwd))
        return 0


def main():
    GLib.set_prgname("pi-terminal")
    GLib.set_application_name("Terminal")
    app = TermApp()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
