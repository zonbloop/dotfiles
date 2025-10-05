#!/usr/bin/env python3
"""
Memento Mori wallpaper generator (v2)
- Cleaner layout (no overlap), better typography
- Support for arranging years into multiple columns (e.g., 2 tall columns of years)
- KDE fallback robustness is preserved

Requires: Pillow
pip install --user pillow
"""
from __future__ import annotations
import os, shutil, subprocess
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
    # Core
    birthdate: str = "2000-06-18"
    expected_years: int = 75
    width: int = 2560
    height: int = 1440
    output_path: str = os.path.expanduser("~/.local/share/memento_mori/wallpaper.png")

    # Visuals
    dark_theme: bool = True
    title: str = "Memento Mori"
    font_path: str | None = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    show_today: bool = True
    show_year_ticks: bool = True  # small year markers at left of each row-block

    # Grid
    weeks_per_year: int = 52
    dot_radius: int = 6
    gap: int = 9
    margin_top: int = 180
    margin_bottom: int = 90
    margin_sides: int = 120

    # Arrange years into multiple vertical blocks placed side-by-side.
    year_columns: int = 2
    block_gap: int = 120  # horizontal gap between year blocks

    # Wallpaper application
    set_wallpaper: bool = True

cfg = Config()
# --------------------- END CONFIG ---------------------

def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def life_fraction(birth: date, expected_years: int, today: date | None = None) -> Tuple[float, int, int, int]:
    if today is None:
        today = date.today()
    # estimate end date (handle Feb 29 safely)
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
    total_cells = cfg.weeks_per_year * cfg.expected_years
    current_cell = int(frac * total_cells)
    current_cell = max(0, min(total_cells - 1, current_cell))
    return frac, max(0, days_lived), max(1, days_total), current_cell

def format_duration(days: int) -> str:
    years = days // 365
    rem = days % 365
    months = rem // 30
    d = rem % 30
    parts = []
    if years: parts.append(f"{years}y")
    if months: parts.append(f"{months}m")
    if d: parts.append(f"{d}d")
    return " ".join(parts) if parts else "0d"

def pick_colors(dark: bool):
    if dark:
        bg = (17, 18, 20); fg = (235, 238, 243); muted = (145, 150, 160)
        active = (88, 176, 255); filled = (220, 225, 232); empty = (70, 74, 82); grid_shadow = (28, 30, 34)
    else:
        bg = (246, 248, 251); fg = (24, 28, 33); muted = (120, 126, 134)
        active = (0, 110, 220); filled = (30, 36, 44); empty = (198, 204, 212); grid_shadow = (225, 229, 235)
    return bg, fg, muted, active, filled, empty, grid_shadow

def try_font(size: int):
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
    bg, fg, muted, active, filled, empty, grid_shadow = pick_colors(cfg.dark_theme)

    img = Image.new("RGB", (cfg.width, cfg.height), bg)
    d = ImageDraw.Draw(img)

    # Typography
    title_font = try_font(96)
    sub_font = try_font(40)
    small_font = try_font(26)

    # Title
    title_w, title_h = d.textsize(cfg.title, font=title_font)
    d.text(((cfg.width - title_w) // 2, 40), cfg.title, fill=fg, font=title_font)

    # Stats under title
    pct = f"{frac*100:0.2f}%"
    lived = format_duration(days_lived)
    remaining = format_duration(max(0, days_total - days_lived))
    stats_line = f"Lived: {lived}   •   Remaining: {remaining}   •   {pct}"
    stats_w, stats_h = d.textsize(stats_line, font=sub_font)
    stats_y = 40 + title_h + 18
    d.text(((cfg.width - stats_w) // 2, stats_y), stats_line, fill=muted, font=sub_font)

    # Legend below stats
    legend = "Each dot = 1 week   •   52 columns = one year"
    leg_w, leg_h = d.textsize(legend, font=small_font)
    legend_y = stats_y + stats_h + 18
    d.text(((cfg.width - leg_w) // 2, legend_y), legend, fill=muted, font=small_font)

    # Grid geometry
    cols = cfg.weeks_per_year
    rows_total = cfg.expected_years
    year_cols = max(1, cfg.year_columns)
    rows_per_block = [(rows_total // year_cols) + (1 if i < (rows_total % year_cols) else 0) for i in range(year_cols)]

    radius = cfg.dot_radius
    gap = cfg.gap
    margin_top = max(cfg.margin_top, legend_y + leg_h + 26)

    grid_w = cols * (radius * 2) + (cols - 1) * gap
    block_w = grid_w
    total_w = year_cols * block_w + (year_cols - 1) * cfg.block_gap
    start_x = (cfg.width - total_w) // 2
    y = margin_top

    def draw_block(x_left: int, y_top: int, block_rows: int, year_offset: int):
        # subtle outline
        pad = 24
        block_h = block_rows * (radius*2) + (block_rows - 1) * gap + 2*pad
        d.rectangle((x_left-18, y_top-18, x_left+block_w+18, y_top+block_h-18), fill=None, outline=grid_shadow, width=2)

        # rows
        for r in range(block_rows):
            year_index = year_offset + r
            # year tick every 5
            if cfg.show_year_ticks and (r % 5 == 0 or r == 0):
                label = str(year_index)
                lw, lh = d.textsize(label, font=small_font)
                d.text((x_left - 14 - lw, y_top + r*(2*radius + gap) + radius - lh//2),
                       label, fill=muted, font=small_font)

            for c in range(cols):
                idx_global = year_index * cols + c
                cx = x_left + c * (2*radius + gap) + radius
                cy = y_top + r * (2*radius + gap) + radius
                color = filled if idx_global <= current_cell else empty
                d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)

        # highlight current week if it falls in this block
        if cfg.show_today:
            r_global = current_cell // cols
            if year_offset <= r_global < year_offset + block_rows:
                r_rel = r_global - year_offset
                c = current_cell % cols
                cx = x_left + c * (2*radius + gap) + radius
                cy = y_top + r_rel * (2*radius + gap) + radius
                pad2 = max(3, radius // 2)
                d.rectangle((cx - radius - pad2, cy - radius - pad2, cx + radius + pad2, cy + radius + pad2),
                            outline=active, width=3)

    year_offset = 0
    x = start_x
    for i, rpb in enumerate(rows_per_block):
        draw_block(x, y, rpb, year_offset)
        x += block_w + cfg.block_gap
        year_offset += rpb

    # Footer
    footer = f"Born {birth.isoformat()} • Today {today.isoformat()} • Expectancy {cfg.expected_years}y"
    foot_w, foot_h = d.textsize(footer, font=small_font)
    d.text(((cfg.width - foot_w) // 2, cfg.height - cfg.margin_bottom - foot_h), footer, fill=muted, font=small_font)

    out_path = os.path.abspath(os.path.expanduser(cfg.output_path))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path

def cmd_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None

def set_wallpaper(path: str) -> bool:
    # GNOME
    if cmd_exists("gsettings"):
        uri = f"file://{path}"
        try:
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", uri], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-options", "scaled"], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass
    # KDE Plasma (new)
    kde_cmd = shutil.which("plasma-apply-wallpaperimage")
    if kde_cmd:
        try:
            subprocess.run([kde_cmd, path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass
    # KDE Plasma (fallback via DBus)
    if cmd_exists("qdbus"):
        try:
            script = f"""
var allDesktops = desktops();
for (i=0;i<allDesktops.length;i++) {{
  d = allDesktops[i];
  d.wallpaperPlugin = "org.kde.image";
  d.currentConfigGroup = ["Wallpaper","org.kde.image","General"];
  d.writeConfig("Image","file://{path}");
}}
"""
            subprocess.run(["qdbus", "org.kde.plasmashell", "/PlasmaShell", "evaluateScript", script],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass
    # Wayland (swww)
    if cmd_exists("swww"):
        try:
            subprocess.run(["swww", "img", path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass
    # Sway
    if cmd_exists("swaymsg"):
        try:
            subprocess.run(["swaybg", "-i", path, "-m", "fill"], check=True)
            return True
        except Exception:
            pass
    # X11 fallback
    if cmd_exists("feh"):
        try:
            subprocess.run(["feh", "--bg-fill", path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass
    return False

def main():
    out = draw_wallpaper()
    print(f"Generated: {out}")
    if cfg.set_wallpaper:
        ok = set_wallpaper(out)
        print("Wallpaper updated." if ok else "Could not set wallpaper automatically.")

if __name__ == "__main__":
    main()
