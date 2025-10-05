#!/usr/bin/env python3
"""
Memento Mori wallpaper generator for Linux
- Draws a 52×N grid (weeks × years) showing life progress
- Writes a PNG
- Optionally tries to set your desktop wallpaper automatically

Requires: Python 3, Pillow
pip install --user pillow

Edit the CONFIG block below to set your birthdate, expected years, output path, etc.
"""
from __future__ import annotations
import math
import os
import shutil
import subprocess
from datetime import datetime, date
from dataclasses import dataclass
from typing import Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as e:
    raise SystemExit("Pillow is required. Install with: pip install --user pillow") from e

# ----------------------- CONFIG -----------------------
@dataclass
class Config:
    # Your birthdate (YYYY-MM-DD)
    birthdate: str = "2000-06-18"
    # Expected lifespan in years (e.g., 90)
    expected_years: int = 60

    # Output image size (pixels)
    width: int = 2560
    height: int = 1440

    # Path to save the generated image (use an absolute path)
    output_path: str = os.path.expanduser("~/.local/share/memento_mori/wallpaper.png")

    # Theme & style
    dark_theme: bool = True
    title: str = "Memento Mori"
    show_today: bool = True  # draw a highlight box for the current week
    font_path: str | None = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # fallback to PIL default if missing
    # Dot/grid options
    columns: int = 52  # weeks per year
    dot_radius: int = 7  # circle radius (px)
    gap: int = 10       # spacing between dots (px)
    margin_top: int = 200
    margin_sides: int = 140

    # Try to set wallpaper after generating
    set_wallpaper: bool = True

cfg = Config()
# --------------------- END CONFIG ---------------------


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def life_fraction(birth: date, expected_years: int, today: date | None = None) -> Tuple[float, int, int, int]:
    """
    Returns (fraction_lived, days_lived, days_total, week_index).
    week_index is based on a uniform split of total days into columns*rows cells.
    """
    if today is None:
        today = date.today()
    death = date(birth.year + expected_years, birth.month, birth.day)
    # Handle Feb 29 gracefully by moving to Feb 28 on non-leap years
    try:
        death = date(birth.year + expected_years, birth.month, birth.day)
    except ValueError:
        if birth.month == 2 and birth.day == 29:
            death = date(birth.year + expected_years, 2, 28)
        else:
            raise

    days_lived = (today - birth).days
    days_total = (death - birth).days
    frac = max(0.0, min(1.0, days_lived / days_total)) if days_total > 0 else 1.0

    total_cells = cfg.columns * cfg.expected_years
    current_cell = int(frac * total_cells)
    # Clamp
    current_cell = max(0, min(total_cells - 1, current_cell))
    return frac, max(0, days_lived), max(1, days_total), current_cell


def format_duration(days: int) -> str:
    years = days // 365
    rem = days % 365
    months = rem // 30
    d = rem % 30
    parts = []
    if years:
        parts.append(f"{years}y")
    if months:
        parts.append(f"{months}m")
    if d:
        parts.append(f"{d}d")
    return " ".join(parts) if parts else "0d"


def pick_colors(dark: bool):
    if dark:
        bg = (15, 15, 18)
        fg = (230, 233, 238)
        muted = (120, 126, 134)
        active = (90, 180, 255)  # accent for current week
        filled = (210, 215, 222)
        empty = (60, 64, 72)
    else:
        bg = (245, 247, 250)
        fg = (20, 24, 28)
        muted = (110, 116, 124)
        active = (0, 110, 220)
        filled = (30, 36, 44)
        empty = (200, 206, 214)
    return bg, fg, muted, active, filled, empty


def try_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if cfg.font_path and os.path.exists(cfg.font_path):
        try:
            return ImageFont.truetype(cfg.font_path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_wallpaper() -> str:
    birth = parse_date(cfg.birthdate)
    today = date.today()
    frac, days_lived, days_total, current_cell = life_fraction(birth, cfg.expected_years, today)

    bg, fg, muted, active, filled, empty = pick_colors(cfg.dark_theme)
    img = Image.new("RGB", (cfg.width, cfg.height), bg)
    d = ImageDraw.Draw(img)

    # Title and stats
    title_font = try_font(96)
    sub_font = try_font(40)
    small_font = try_font(28)

    title_w, title_h = d.textsize(cfg.title, font=title_font)
    d.text(((cfg.width - title_w) // 2, 60), cfg.title, fill=fg, font=title_font)

    pct = f"{frac*100:0.2f}%"
    lived = format_duration(days_lived)
    remaining = format_duration(max(0, days_total - days_lived))

    stats_line = f"Lived: {lived}   •   Remaining: {remaining}   •   {pct}"
    stats_w, stats_h = d.textsize(stats_line, font=sub_font)
    d.text(((cfg.width - stats_w) // 2, 60 + title_h + 20), stats_line, fill=muted, font=sub_font)

    # Grid geometry
    rows = cfg.expected_years
    cols = cfg.columns
    radius = cfg.dot_radius
    gap = cfg.gap
    margin_top = cfg.margin_top
    margin_sides = cfg.margin_sides

    grid_w = cols * (radius * 2) + (cols - 1) * gap
    grid_h = rows * (radius * 2) + (rows - 1) * gap

    start_x = (cfg.width - grid_w) // 2
    start_y = margin_top

    # Draw legend
    legend = "Each circle = 1 week • Rows = years • 52 columns per year"
    leg_w, _ = d.textsize(legend, font=small_font)
    d.text(((cfg.width - leg_w) // 2, start_y - 50), legend, fill=muted, font=small_font)

    # Draw grid of dots
    total_cells = rows * cols
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            cx = start_x + c * (2 * radius + gap) + radius
            cy = start_y + r * (2 * radius + gap) + radius

            color = filled if idx <= current_cell else empty
            d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color, outline=None)

    # Highlight today's box
    if cfg.show_today:
        r = current_cell // cols
        c = current_cell % cols
        cx = start_x + c * (2 * radius + gap) + radius
        cy = start_y + r * (2 * radius + gap) + radius
        pad = max(3, radius // 2)
        d.rectangle(
            (cx - radius - pad, cy - radius - pad, cx + radius + pad, cy + radius + pad),
            outline=active, width=3
        )

    # Footer
    footer = f"Born {birth.isoformat()} • Today {today.isoformat()} • Expectancy {cfg.expected_years}y"
    foot_w, _ = d.textsize(footer, font=small_font)
    d.text(((cfg.width - foot_w) // 2, start_y + grid_h + 40), footer, fill=muted, font=small_font)

    # Ensure output dir
    out_path = os.path.abspath(os.path.expanduser(cfg.output_path))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path


def cmd_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def set_wallpaper(path: str) -> bool:
    """Try a few common desktop environments; return True on success."""
    # 1) GNOME (gsettings)
    if cmd_exists("gsettings"):
        # Set both light/dark URIs when available
        uri = f"file://{path}"
        try:
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", uri],
                check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.background", "picture-options", "scaled"],
                check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            pass

    # 2) KDE Plasma (plasma-apply-wallpaperimage - Plasma 5.26+)
    if cmd_exists("plasma-apply-wallpaperimage"):
        try:
            subprocess.run(["plasma-apply-wallpaperimage", path], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

    # 3) Wayland (swww)
    if cmd_exists("swww"):
        try:
            subprocess.run(["swww", "img", path], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

    # 4) Sway (swaymsg + swaybg)
    if cmd_exists("swaymsg"):
        try:
            # Try via swaybg (will replace current background)
            subprocess.run(["swaybg", "-i", path, "-m", "fill"], check=True)
            return True
        except Exception:
            pass

    # 5) X11 lightweight (feh)
    if cmd_exists("feh"):
        try:
            subprocess.run(["feh", "--bg-fill", path], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

    return False


def main():
    out = draw_wallpaper()
    print(f"Generated: {out}")
    if cfg.set_wallpaper:
        ok = set_wallpaper(out)
        if ok:
            print("Wallpaper updated.")
        else:
            print("Could not set wallpaper automatically. Set it manually using your DE's settings.")


if __name__ == "__main__":
    main()
