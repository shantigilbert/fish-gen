"""A dark, flat ttk theme for the studio, drawn with Pillow so it needs no extra packages.

Tk's built-in themes look dated and the nice third-party ones are extra dependencies, so this
builds a theme on top of "clam" and swaps its bevelled elements for antialiased images: rounded
buttons and fields, round slider knobs, pill scrollbars and underlined tabs.
"""

from __future__ import annotations

import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from PIL import Image, ImageDraw, ImageTk

THEME = "fishgen"

BG = "#1b1d23"
FIELD = "#262a32"
HOVER = "#2f343e"
PRESSED = "#383e4a"
BORDER = "#363b46"
TRACK = "#3a404b"
TEXT = "#e6e8ec"
MUTED = "#8a92a0"
DISABLED = "#5b616c"
ACCENT = "#35b5c6"
ACCENT_HOVER = "#52c8d7"
ACCENT_PRESSED = "#2a98a7"
ON_ACCENT = "#0d1b1e"

SS = 4  # supersampling, for smooth curves

_FONTS = {
    "win": ("Segoe UI",),
    "darwin": ("SF Pro Text", ".AppleSystemUIFont", "Helvetica Neue"),
    "other": ("Inter", "Noto Sans", "Cantarell", "Ubuntu", "DejaVu Sans"),
}


def _rgba(color: str) -> tuple[int, int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), 255


class _Painter:
    """Draws element images in logical pixels, scaled for the screen's DPI."""

    def __init__(self, root: tk.Misc):
        self.root = root
        self.k = max(1.0, float(root.tk.call("tk", "scaling")) / (96 / 72))
        self.images: list[ImageTk.PhotoImage] = []  # Tk drops images nothing in Python refers to

    def px(self, n: float) -> int:
        return max(1, round(n * self.k))

    def image(self, w: float, h: float, draw, bg: str = BG) -> ImageTk.PhotoImage:
        # Flattened onto the color behind it: Tk on X11 draws an image with partial transparency by
        # reading the screen back and blending it, which made hovering and switching tabs sluggish.
        w, h = self.px(w), self.px(h)
        big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        draw(ImageDraw.Draw(big), self.k * SS, w * SS, h * SS)
        small = Image.alpha_composite(Image.new("RGBA", (w, h), _rgba(bg)), big.resize((w, h), Image.LANCZOS))
        img = ImageTk.PhotoImage(small.convert("RGB"), master=self.root)
        self.images.append(img)
        return img

    def box(self, w, h, r, fill=None, outline=None, line=1.0):
        def draw(d, s, W, H):
            inset = line * s / 2 if outline else 0
            d.rounded_rectangle((inset, inset, W - 1 - inset, H - 1 - inset), r * s,
                                fill=_rgba(fill) if fill else None, outline=_rgba(outline) if outline else None,
                                width=round(line * s) if outline else 0)
        return self.image(w, h, draw)

    def circle(self, d, fill=None, outline=None, line=1.0, dot=None):
        def draw(dr, s, W, H):
            inset = line * s / 2 if outline else 0
            dr.ellipse((inset, inset, W - 1 - inset, H - 1 - inset), fill=_rgba(fill) if fill else None,
                       outline=_rgba(outline) if outline else None, width=round(line * s) if outline else 0)
            if dot:
                q = W * 0.32
                dr.ellipse((q, q, W - 1 - q, H - 1 - q), fill=_rgba(dot))
        return self.image(d, d, draw)

    def check(self, d, fill, mark):
        def draw(dr, s, W, H):
            dr.rounded_rectangle((0, 0, W - 1, H - 1), 4 * s, fill=_rgba(fill))
            dr.line([(W * 0.25, H * 0.52), (W * 0.43, H * 0.70), (W * 0.76, H * 0.32)], fill=_rgba(mark),
                    width=round(2 * s), joint="curve")
        return self.image(d, d, draw)

    def chevron(self, w, h, color, up=False, bg=FIELD):
        def draw(dr, s, W, H):
            cx, cy, a = W / 2, H / 2, 3.2 * s
            dy = -a / 2 if up else a / 2
            dr.line([(cx - a, cy - dy), (cx, cy + dy), (cx + a, cy - dy)], fill=_rgba(color),
                    width=round(1.6 * s), joint="curve")
        return self.image(w, h, draw, bg)

    def track(self, w, h, thickness, color):
        def draw(dr, s, W, H):
            t = thickness * s
            dr.rounded_rectangle((0, (H - t) / 2, W - 1, (H + t) / 2), t / 2, fill=_rgba(color))
        return self.image(w, h, draw)

    def pill(self, w, h, inner, color):
        def draw(dr, s, W, H):
            m = (W - inner * s) / 2
            dr.rounded_rectangle((m, m, W - 1 - m, H - 1 - m), inner * s / 2, fill=_rgba(color))
        return self.image(w, h, draw)

    def underline(self, w, h, thickness, color):
        def draw(dr, s, W, H):
            if color:
                dr.rounded_rectangle((0, H - thickness * s, W - 1, H - 1), thickness * s / 2, fill=_rgba(color))
        return self.image(w, h, draw)


def _pick_font() -> str:
    key = "win" if sys.platform.startswith("win") else sys.platform if sys.platform == "darwin" else "other"
    families = set(tkfont.families())
    return next((f for f in _FONTS[key] if f in families), tkfont.nametofont("TkDefaultFont").actual("family"))


def apply(root: tk.Tk) -> None:
    """Install the theme and the app's named styles: Accent/Chip.TButton, Section/Hint/Value/Status.TLabel."""
    style = ttk.Style(root)
    if THEME in style.theme_names():
        style.theme_use(THEME)
        return
    p = _Painter(root)
    root._fishgen_theme_images = p.images  # keep them alive as long as the window

    family = _pick_font()
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
        tkfont.nametofont(name).configure(family=family, size=10)
    section_font = (family, 10, "bold")
    small_font = (family, 9)

    E = style.element_create
    style.theme_create(THEME, parent="clam")
    style.theme_use(THEME)

    # ttk fills a widget by tiling the middle of its image, so the images below are made about as big
    # as the widgets they cover: one or two draws each instead of hundreds of tiny ones. Their width and
    # height options then stop the big image from setting how big the widget asks to be.
    W, H = 160, 36
    small = dict(width=p.px(14), height=p.px(14))

    # Buttons
    btn = dict(border=p.px(6), padding=p.px(1), sticky="nsew", **small)
    E("Button.button", "image", p.box(W, H, 6, FIELD, BORDER),
      ("disabled", p.box(W, H, 6, BG, BORDER)), ("pressed", p.box(W, H, 6, PRESSED, BORDER)),
      ("active", p.box(W, H, 6, HOVER, MUTED)), **btn)
    E("Accent.Button.button", "image", p.box(W, H, 6, ACCENT),
      ("disabled", p.box(W, H, 6, BG, BORDER)), ("pressed", p.box(W, H, 6, ACCENT_PRESSED)),
      ("active", p.box(W, H, 6, ACCENT_HOVER)), **btn)
    for name, element in (("TButton", "Button.button"), ("Accent.TButton", "Accent.Button.button")):
        style.layout(name, [(element, {"sticky": "nswe", "children": [
            ("Button.padding", {"sticky": "nswe", "children": [("Button.label", {"sticky": "nswe"})]})]})])
    style.configure("TButton", padding=(p.px(9), p.px(2)), anchor="center", foreground=TEXT)
    style.map("TButton", foreground=[("disabled", DISABLED)])
    style.configure("Chip.TButton", padding=(p.px(1), p.px(1)))
    style.configure("Accent.TButton", padding=(p.px(14), p.px(4)), foreground=ON_ACCENT, font=section_font)
    style.map("Accent.TButton", foreground=[("disabled", DISABLED)])

    # Text fields, drop-downs and spinners share one rounded field
    field = (p.box(W, H, 6, FIELD, BORDER), ("disabled", p.box(W, H, 6, BG, BORDER)),
             ("focus", p.box(W, H, 6, FIELD, ACCENT)), ("hover", p.box(W, H, 6, FIELD, MUTED)))
    for name in ("Entry.field", "Combobox.field", "Spinbox.field"):
        E(name, "image", *field, border=p.px(6), padding=p.px(1), sticky="nsew", **small)
    E("Combobox.downarrow", "image", p.chevron(20, 16, MUTED), ("disabled", p.chevron(20, 16, DISABLED, bg=BG)),
      ("active", p.chevron(20, 16, TEXT)), sticky="")
    E("Spinbox.uparrow", "image", p.chevron(16, 9, MUTED, up=True), ("active", p.chevron(16, 9, TEXT, up=True)),
      sticky="")
    E("Spinbox.downarrow", "image", p.chevron(16, 9, MUTED), ("active", p.chevron(16, 9, TEXT)), sticky="")
    style.layout("TEntry", [("Entry.field", {"sticky": "nswe", "children": [
        ("Entry.padding", {"sticky": "nswe", "children": [("Entry.textarea", {"sticky": "nswe"})]})]})])
    style.layout("TCombobox", [("Combobox.field", {"sticky": "nswe", "children": [
        ("Combobox.downarrow", {"side": "right", "sticky": "ns"}),
        ("Combobox.padding", {"sticky": "nswe", "children": [("Combobox.textarea", {"sticky": "nswe"})]})]})])
    style.layout("TSpinbox", [("Spinbox.field", {"sticky": "nswe", "children": [
        ("null", {"side": "right", "sticky": "", "children": [
            ("Spinbox.uparrow", {"side": "top", "sticky": "e"}),
            ("Spinbox.downarrow", {"side": "bottom", "sticky": "e"})]}),
        ("Spinbox.padding", {"sticky": "nswe", "children": [("Spinbox.textarea", {"sticky": "nswe"})]})]})])
    for name in ("TEntry", "TCombobox", "TSpinbox"):
        style.configure(name, padding=(p.px(7), p.px(2), p.px(3), p.px(2)), foreground=TEXT, insertcolor=TEXT,
                        selectbackground=ACCENT, selectforeground=ON_ACCENT, fieldbackground=FIELD)
        style.map(name, foreground=[("disabled", DISABLED)], fieldbackground=[("disabled", BG)],
                  selectbackground=[("readonly", FIELD)], selectforeground=[("readonly", TEXT)])

    # Sliders: a thin track and a round knob
    E("Horizontal.Scale.trough", "image", p.track(480, 16, 4, TRACK), border=(p.px(8), 0), sticky="ew", width=p.px(24))
    E("Horizontal.Scale.slider", "image", p.circle(16, ACCENT),
      ("disabled", p.circle(16, DISABLED)), ("pressed", p.circle(16, ACCENT_PRESSED)),
      ("active", p.circle(16, ACCENT_HOVER)), sticky="")
    style.layout("Horizontal.TScale", [("Horizontal.Scale.trough", {"sticky": "nswe", "children": [
        ("Horizontal.Scale.slider", {"side": "left", "sticky": ""})]})])

    # Check boxes and radio buttons
    off = dict(fill=FIELD, outline=MUTED, line=1.3)
    E("Checkbutton.indicator", "image", p.box(17, 17, 4, **off),
      ("disabled", "selected", p.check(17, DISABLED, BG)), ("disabled", p.box(17, 17, 4, BG, BORDER)),
      ("pressed", "selected", p.check(17, ACCENT_PRESSED, ON_ACCENT)),
      ("active", "selected", p.check(17, ACCENT_HOVER, ON_ACCENT)), ("selected", p.check(17, ACCENT, ON_ACCENT)),
      ("active", p.box(17, 17, 4, HOVER, TEXT, 1.3)), width=p.px(25), sticky="w")
    E("Radiobutton.indicator", "image", p.circle(17, **off),
      ("disabled", "selected", p.circle(17, DISABLED, dot=BG)), ("disabled", p.circle(17, BG, BORDER)),
      ("active", "selected", p.circle(17, ACCENT_HOVER, dot=ON_ACCENT)),
      ("selected", p.circle(17, ACCENT, dot=ON_ACCENT)),
      ("active", p.circle(17, HOVER, TEXT, 1.3)), width=p.px(25), sticky="w")
    for name in ("Checkbutton", "Radiobutton"):
        style.layout(f"T{name}", [(f"{name}.padding", {"sticky": "nswe", "children": [
            (f"{name}.indicator", {"side": "left", "sticky": ""}),
            (f"{name}.label", {"side": "left", "sticky": "w"})]})])
        style.configure(f"T{name}", padding=(0, p.px(1)), foreground=TEXT)
        style.map(f"T{name}", foreground=[("disabled", DISABLED)], background=[("active", BG)])

    # Scrollbars: a slim pill with no arrows
    E("Vertical.Scrollbar.trough", "image", p.box(10, 900, 0, BG), border=0, sticky="ns", height=p.px(20))
    E("Vertical.Scrollbar.thumb", "image", p.pill(10, 300, 5, TRACK),
      ("pressed", p.pill(10, 300, 6, MUTED)), ("active", p.pill(10, 300, 6, DISABLED)),
      border=(0, p.px(6)), sticky="nsew", height=p.px(20))
    style.layout("Vertical.TScrollbar", [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
        ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])

    # Tabs: plain text, the open one underlined in the accent color
    E("Notebook.tab", "image", p.underline(160, 48, 2, None), ("selected", p.underline(160, 48, 2, ACCENT)),
      ("active", p.underline(160, 48, 2, BORDER)), border=(p.px(4), p.px(4), p.px(4), p.px(4)), sticky="nsew", **small)
    style.layout("TNotebook.Tab", [("Notebook.tab", {"sticky": "nswe", "children": [
        ("Notebook.padding", {"side": "top", "sticky": "nswe", "children": [
            ("Notebook.label", {"side": "top", "sticky": ""})]})]})])
    style.configure("TNotebook", tabmargins=(0, 0, 0, 0), borderwidth=0, bordercolor=BG)
    style.configure("TNotebook.Tab", padding=(p.px(10), p.px(4)), foreground=MUTED, font=section_font)
    style.map("TNotebook.Tab", foreground=[("selected", TEXT), ("active", TEXT)], expand=[])

    # Group boxes: a rounded outline with the title above it
    E("Labelframe.border", "image", p.box(900, 400, 8, None, BORDER), border=p.px(9), padding=p.px(2), sticky="nsew",
      width=p.px(20), height=p.px(20))
    style.configure("TLabelframe", labeloutside=True, labelmargins=(p.px(2), 0, 0, p.px(2)))
    style.configure("TLabelframe.Label", foreground=TEXT, font=section_font)

    # Everything else, plus the app's own label styles
    style.configure(".", background=BG, foreground=TEXT, bordercolor=BORDER, lightcolor=BG, darkcolor=BG,
                    troughcolor=BG, focuscolor=ACCENT, selectbackground=ACCENT, selectforeground=ON_ACCENT,
                    insertcolor=TEXT, font="TkDefaultFont")
    style.map(".", foreground=[("disabled", DISABLED)])
    style.configure("TSeparator", background=BORDER)
    style.configure("Sash", sashthickness=p.px(6), gripcount=0, background=BG, lightcolor=BG, bordercolor=BG)
    style.configure("Section.TLabel", font=section_font, foreground=TEXT)
    style.configure("Hint.TLabel", font=small_font, foreground=MUTED)
    style.configure("Value.TLabel", font=small_font, foreground=MUTED)
    style.configure("Status.TLabel", font=small_font, foreground=MUTED)
    root.configure(background=BG)

    # A ttk widget only repaints when its size changes. When one just moves (the status bar sliding down
    # as the window goes full screen), X carries the old pixels along with it, and it kept showing a
    # stale piece of the preview. The widgets inside a moved one move too without being told, so a move
    # repaints the widget and everything in it. Under clam these widgets leave their background to X,
    # which a repaint doesn't clear, so they get a fill.
    for name in ("TFrame", "TLabel", "TCheckbutton", "TRadiobutton"):
        style.layout(name, [(f"{name[1:]}.fill", {"sticky": "nswe", "children": style.layout(name)})])

    def repaint(w: tk.Misc):
        if w.winfo_class().startswith("T"):
            w.event_generate("<Expose>")  # ttk merges repeat requests into one redraw
        for child in w.winfo_children():
            if child.winfo_ismapped():
                repaint(child)

    def configured(event):
        w = event.widget
        if isinstance(w, tk.Misc) and w.winfo_class().startswith("T"):
            repaint(w)
    root.bind_all("<Configure>", configured, add="+")
