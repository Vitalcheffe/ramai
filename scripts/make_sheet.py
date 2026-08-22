"""Generate the printable A4 game sheet for ramai.

The sheet has 5 zones:
  - MONTRE     (square, ~8cm)    — where humans show cards face-up to camera
  - ZONE IA    (15 numbered slots) — AI's hand laid face-down by position
  - TALON      (small rectangle)   — face-down stock pile
  - DEFAUSSE   (small rectangle)   — face-up discard pile
  - CENTRE     (large rectangle)   — melds laid by both players

Print on A4 paper. Place on the table. The camera calibrates by locating
the 5 zones at startup. All subsequent detection happens within these
fixed regions.

Usage:
    python scripts/make_sheet.py
    → outputs assets/ramai_sheet.pdf
"""
from __future__ import annotations
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# Try to register a CJK-friendly font if available, else default to Helvetica
def _register_fonts():
    """Try to load Tinos or DejaVu for unicode card symbols."""
    try:
        # Tinos is a Times-like font that supports Latin Extended
        pdfmetrics.registerFont(TTFont('Tinos', '/usr/share/fonts/truetype/english/Tinos-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Tinos-Bold', '/usr/share/fonts/truetype/english/Tinos-Bold.ttf'))
        return 'Tinos', 'Tinos-Bold'
    except Exception:
        pass
    try:
        pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
        return 'DejaVu', 'DejaVu-Bold'
    except Exception:
        pass
    return 'Helvetica', 'Helvetica-Bold'


def make_sheet(output_path: str = "assets/ramai_sheet.pdf") -> str:
    """Generate the A4 calibration sheet PDF."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    c = canvas.Canvas(output_path, pagesize=A4)
    w, h = A4  # 595 x 842 pt = 210 x 297 mm

    body_font, bold_font = _register_fonts()

    # --- Title ---
    c.setFont(bold_font, 22)
    c.setFillColor(black)
    c.drawCentredString(w/2, h - 25*mm, "ramai — calibration sheet")
    c.setFont(body_font, 10)
    c.drawCentredString(w/2, h - 32*mm, "Print on A4. Place on the table. The camera calibrates the 5 zones at startup.")
    c.drawCentredString(w/2, h - 36*mm, "Author: Amine Harch El Korane  ·  License: MIT  ·  github.com/Vitalcheffe/ramai")

    # --- Zone parameters ---
    margin_x = 15*mm
    zone_color = HexColor("#222222")
    zone_fill = HexColor("#fafafa")
    label_color = HexColor("#000000")

    # Zone Y positions (top to bottom)
    y_top = h - 50*mm  # below title
    y_bot = 15*mm      # bottom margin

    # Available vertical space
    avail_h = y_top - y_bot

    # --- Zone 1: MONTRE (square, ~8cm) — top-left ---
    montre_size = 80*mm
    montre_x = margin_x
    montre_y = y_top - montre_size
    _draw_zone(c, montre_x, montre_y, montre_size, montre_size,
               "MONTRE", "show one card here, face-up",
               body_font, bold_font)

    # --- Zone 2: TALON + DEFAUSSE (side by side) — top-right ---
    pile_w = 60*mm
    pile_h = 50*mm
    pile_x = w - margin_x - pile_w
    talon_y = y_top - pile_h
    _draw_zone(c, pile_x, talon_y, pile_w, pile_h,
               "TALON", "face-down stock",
               body_font, bold_font)

    defausse_y = talon_y - pile_h - 10*mm
    _draw_zone(c, pile_x, defausse_y, pile_w, pile_h,
               "DEFAUSSE", "face-up discard pile",
               body_font, bold_font)

    # --- Zone 3: ZONE IA (15 numbered slots, 3 rows × 5 cols) ---
    zone_ia_top = defausse_y - 10*mm
    zone_ia_bot_label_h = 6*mm
    zone_ia_h = 60*mm
    zone_ia_y = zone_ia_top - zone_ia_h
    zone_ia_w = w - 2*margin_x - (pile_w + 5*mm) - 5*mm  # left of piles
    zone_ia_x = margin_x
    _draw_zone(c, zone_ia_x, zone_ia_y, zone_ia_w, zone_ia_h,
               "ZONE IA (15 emplacements)", "AI's hand, face-down, ordered by position",
               body_font, bold_font)
    # Draw 15 numbered slots inside (3 rows × 5 cols)
    slot_pad = 5*mm
    slot_w = (zone_ia_w - 2*slot_pad - 4*2*mm) / 5
    slot_h = (zone_ia_h - 2*slot_pad - zone_ia_bot_label_h - 2*2*mm) / 3
    for i in range(15):
        row = i // 5
        col = i % 5
        sx = zone_ia_x + slot_pad + col * (slot_w + 2*mm)
        sy = zone_ia_y + slot_pad + zone_ia_bot_label_h + (2 - row) * (slot_h + 2*mm)
        c.setStrokeColor(HexColor("#666666"))
        c.setLineWidth(0.5)
        c.setDash(2, 2)
        c.rect(sx, sy, slot_w, slot_h, stroke=1, fill=0)
        c.setDash()
        c.setFont(body_font, 9)
        c.setFillColor(label_color)
        c.drawCentredString(sx + slot_w/2, sy + slot_h/2 - 2, str(i+1))

    # --- Zone 4: CENTRE (large rectangle, bottom) ---
    centre_h = 80*mm
    centre_y = y_bot + 5*mm
    centre_x = margin_x
    centre_w = w - 2*margin_x
    _draw_zone(c, centre_x, centre_y, centre_w, centre_h,
               "CENTRE", "melds laid by both players",
               body_font, bold_font)

    # --- Footer ---
    c.setFont(body_font, 8)
    c.setFillColor(HexColor("#666666"))
    c.drawCentredString(w/2, 8*mm,
                        "All 5 zones must be visible to the camera. "
                        "Place cards inside the zones. The AI detects by zone, not by free-form position.")

    c.showPage()
    c.save()
    return output_path


def _draw_zone(c: canvas.Canvas, x: float, y: float, w: float, h: float,
               label: str, sublabel: str, body_font: str, bold_font: str):
    """Draw a labeled zone rectangle."""
    # Fill
    c.setFillColor(HexColor("#fafafa"))
    c.setStrokeColor(HexColor("#222222"))
    c.setLineWidth(1.5)
    c.rect(x, y, w, h, stroke=1, fill=1)

    # Label (top-left of zone)
    c.setFillColor(HexColor("#000000"))
    c.setFont(bold_font, 12)
    c.drawString(x + 3*mm, y + h - 6*mm, label)
    c.setFont(body_font, 8)
    c.setFillColor(HexColor("#666666"))
    c.drawString(x + 3*mm, y + h - 9*mm, sublabel)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="assets/ramai_sheet.pdf")
    args = p.parse_args()
    path = make_sheet(args.output)
    size_kb = os.path.getsize(path) / 1024
    print(f"✓ Generated: {path} ({size_kb:.1f} KB)")
