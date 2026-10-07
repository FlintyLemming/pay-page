#!/usr/bin/env python3
"""Redraw the WeChat Pay / Alipay QR codes used by index.html.

The page doesn't use crops of the official posters. Each code is re-encoded
from its payload (the text inside the QR code) and drawn in the page's style,
so if a payment code ever changes, decode the new poster with any QR reader,
update `data` below and rerun:

    pip install segno pillow        # pillow is optional, it only shrinks the PNGs
    python tools/build_qr.py

PNG export uses a local Chrome or Edge in headless mode. Set CHROME=/path/to/browser
if it isn't found automatically.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import segno

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

INK = "#16181D"
QUIET = 3          # quiet zone, in modules
MODULE_PX = 24     # output resolution per module
CORNER = 0.38      # rounding of outer module corners
FILLET = 0.25      # rounding of inner (concave) corners
EYE_RADII = (2.0, 1.1, 0.8)   # finder pattern: outer ring, ring hole, centre
LOGO_ZONE = 9      # modules cleared in the middle for the logo (error level H keeps this safe)

# Silhouettes traced from the official logos; the logo colour shows through the cut-outs.
WECHAT_LOGO = (173.1, 152.9, "M29.4 152.6C27.9 151.9 27.6 150.2 28.3 147.4C28.5 146.7 29.2 144 29.9 141.4C30.6 138.7 31.3 135.9 31.6 135.1C32.9 130.5 32.2 129.1 26.6 124.6C10 111.3 0.4 92.9 0 73.6C-0.1 66.6 1.3 57.9 3.4 52.2C5 47.8 6.5 44.7 8.1 41.9C8.7 40.8 9.6 39.4 10 38.8C18.1 25 36.6 10.9 53.4 5.6C54.3 5.3 56.1 4.8 57.3 4.4C62.2 2.8 67 1.8 73.1 1.1C74.6 0.9 76.4 0.7 77.1 0.6C84.4 -0.5 95 0 105.6 1.9C110.8 2.8 112.5 3.3 119.1 5.5C126.6 8 134.4 11.8 139.8 15.5C145.3 19.3 148.9 22.2 152.6 25.9C157.2 30.4 157.1 31 151.9 33.2C150.8 33.7 149 34.4 147.9 35C146.8 35.5 145.2 36.2 144.3 36.6C141.7 37.7 139.8 38.5 137.8 39.5C136.8 40 134.9 40.8 133.6 41.4C132.3 41.9 130.2 42.8 129.1 43.4C127.9 43.9 125.8 44.8 124.4 45.4C123.1 46 121.3 46.8 120.5 47.2C119.7 47.6 117.9 48.4 116.5 49C115.1 49.6 112.8 50.6 111.4 51.3C110 51.9 107.9 52.9 106.7 53.4C105.5 53.9 103.7 54.7 102.6 55.2C101.5 55.7 99.4 56.7 98 57.3C96.6 57.9 94.6 58.8 93.6 59.3C92.5 59.7 90.7 60.6 89.5 61.1C88.3 61.6 86.4 62.4 85.2 62.9C84.1 63.5 82.2 64.3 81 64.8C79.8 65.4 77.6 66.4 76 67.1C66.6 71.4 65.5 71.4 58.3 66.3C56.8 65.2 54.4 63.5 52.9 62.4C51.4 61.4 49.4 60 48.5 59.3C43.2 55.4 41.7 54.8 40.2 56.1C38.6 57.4 39 58.8 43.4 68.2C44.2 70.1 45.2 72.2 45.4 72.8C45.7 73.4 46.4 75 47.1 76.4C47.7 77.7 48.6 79.7 49.1 80.8C49.5 81.8 50.4 83.8 51.1 85.1C51.7 86.5 52.6 88.5 53.1 89.6C56.7 98.2 59.1 99.2 66.3 94.9C67.3 94.4 68.8 93.5 69.7 93C70.6 92.5 72.3 91.5 73.6 90.8C74.8 90 76.9 88.8 78.3 88C79.7 87.2 81.5 86.1 82.3 85.7C83.1 85.2 84.4 84.4 85.1 84C88 82.4 91.1 80.7 93.3 79.3C94.6 78.5 96.2 77.6 96.8 77.3C97.4 77 98.8 76.2 99.8 75.6C100.8 74.9 102.5 73.9 103.6 73.4C104.6 72.8 106.5 71.7 107.7 71C108.9 70.3 110.5 69.3 111.2 68.9C112 68.5 113.6 67.6 114.8 66.9C117.9 65 122.1 62.6 124.4 61.3C125.4 60.7 126.9 59.8 127.7 59.4C128.4 58.9 129.7 58.2 130.4 57.8C131.6 57.1 134.4 55.5 139.9 52.3C141.2 51.5 143.2 50.4 144.4 49.7C145.7 49 147.2 48.1 147.9 47.7C148.5 47.3 149.9 46.5 150.9 45.9C152 45.3 153.8 44.3 154.9 43.6C163.2 38.6 163.4 38.6 166.1 44C169.5 50.9 171.1 55.9 172.4 64C173.6 71.8 173.4 77 171.4 86.1C168.5 99.6 160.7 112.1 148.6 122.9C146.1 125.1 138.7 130.3 135.8 131.9C131.4 134.3 129.1 135.5 125.8 136.9C124.6 137.3 122.9 138 122 138.4C120.2 139.2 119.6 139.4 114.2 140.9C101.2 144.7 85 145.8 72.1 143.8C66.9 143 64.2 142.5 61.5 141.7C56.6 140.2 54.4 140.3 51.4 141.8C50.3 142.4 45.5 145.1 43.9 146C43.3 146.4 42.1 147.1 41.1 147.7C40.2 148.2 38.3 149.2 37 150C32.1 152.9 30.9 153.3 29.4 152.6Z")
ALIPAY_LOGO = (127.1, 127.0, "M24.5 126.9C11.9 126.1 1.9 116.6 0.2 103.9C0 102.1 0 24.9 0.2 23.1C1.8 10.9 10.9 1.8 23.1 0.2C24.9 0 102.2 0 104.1 0.2C115.1 1.7 123.9 9.5 126.4 20.1C127.1 23.2 127 21 127.1 54.6L127.1 85.5L126.2 85.6C124.8 85.7 124.2 85.7 123.2 85.4C122.6 85.2 121.4 84.9 120.4 84.7C117.7 84.2 112 82.5 107 80.7C101.9 79 100.9 78.6 99.4 78C98.4 77.6 96.4 76.9 94.8 76.4C84.7 73 84.8 73 86.8 69.2C87.7 67.4 88.1 66.7 90.4 61.3C93.3 54.6 95.1 48.5 94.5 47.2C94 46.2 93.2 46.1 81.3 46.1C71.4 46.2 71.8 46.2 71.1 45.4C70.3 44.5 70.2 38.9 71 37.9C71.6 37 70.5 37.1 85.6 37L99.1 36.9L99.7 36.6C101.2 35.8 101.2 33.5 99.7 32.8L99.1 32.4L85.5 32.4C75.5 32.3 71.9 32.3 71.7 32.2C70.5 31.5 70.5 31.2 70.4 24.9C70.4 16.9 70.8 17.4 64.2 17.3C56 17.1 56.3 16.9 56.2 25.1C56.1 30.6 56.1 31 55.5 31.6C54.9 32.3 55.6 32.3 40.8 32.4C27.4 32.4 27.1 32.4 26.6 32.7C25.3 33.3 25 35.3 26.1 36.2C26.9 37 26.3 36.9 40.8 36.9C57.6 37 56 36.5 56.1 41.1C56.2 46.5 57.1 46.2 44.2 46.1C32.5 46.1 31.8 46.2 31.1 47.2C30.7 47.7 30.7 49.3 31.1 49.8C31.9 50.9 30.8 50.9 56 50.9C80.6 50.9 78.7 50.8 79.3 51.7C79.8 52.4 79.1 55.1 77.3 59.1C77.1 59.6 76.7 60.7 76.4 61.4C75.7 63.5 74.2 66.5 73.5 67.1C72.3 68.3 71.7 68.3 66.8 66.7C65.4 66.3 63.7 65.8 62.9 65.5C59 64.3 50 62.2 46.1 61.6C37 60.2 32.4 60.4 26.2 62.5C9.4 68 4.5 87 16.8 98.8C18.3 100.3 19 100.8 22.1 102.3C31.2 106.9 42 106.9 53.4 102.1C54.4 101.7 55.8 101.1 56.5 100.8C58.3 100 62.8 97.2 65.2 95.3C65.9 94.8 67 93.9 67.6 93.4C69.3 92.1 72.2 89.3 74.3 87C77.4 83.6 77.6 83.6 83.1 86.3C87.8 88.5 90.3 89.7 91.9 90.4C92.7 90.7 94 91.3 94.8 91.7C95.5 92 97 92.6 97.9 93C98.9 93.4 100.7 94.1 102 94.7C103.3 95.3 104.4 95.8 104.4 95.8C104.5 95.8 105.4 96.2 106.5 96.7C108.4 97.6 109.6 98.1 113.1 99.6C113.8 99.9 115.4 100.6 116.6 101.1C119.1 102 123.7 103.9 124.5 104.3C125 104.6 125.3 104.6 125.9 104.6C126.9 104.6 126.9 104.5 126.4 106.6C124 117.2 115.7 124.9 104.6 126.7C103.2 126.9 28.1 127.1 24.5 126.9ZM30.5 97.3C20 95.9 13.4 89.7 14.1 82.1C15.5 67.8 37.5 64.2 58.7 74.8C59.3 75.1 60.5 75.6 61.4 75.9C67 78.1 66.8 79.4 59.8 86C50.4 94.8 40.4 98.7 30.5 97.3Z")

CODES = [
    # logo_size: width of the centre logo in modules (the square Alipay mark is drawn a bit smaller to look the same size)
    dict(file="wechat-pay.png", data="wxp://f2f0CEnRkTYvv39_eWRcT6jyGdgYVSm9anRl4_mj8av7k-M",
         eye="#07A650", logo_color="#07C160", logo=WECHAT_LOGO, logo_size=7.0),
    dict(file="alipay.png", data="https://qr.alipay.com/2m618761jsklwq3dlghea29",
         eye="#1677FF", logo_color="#1677FF", logo=ALIPAY_LOGO, logo_size=6.3),
]


def num(v):
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def rounded_rect(x, y, w, h, r):
    a = f"A{num(r)} {num(r)} 0 0 1"
    return (f"M{num(x + r)} {num(y)}H{num(x + w - r)}{a} {num(x + w)} {num(y + r)}"
            f"V{num(y + h - r)}{a} {num(x + w - r)} {num(y + h)}H{num(x + r)}{a} {num(x)} {num(y + h - r)}"
            f"V{num(y + r)}{a} {num(x + r)} {num(y)}Z")


def module(x, y, tl, tr, br, bl):
    """A dark module whose corners are rounded only where it doesn't touch a neighbour."""
    d = f"M{num(x + tl)} {num(y)}H{num(x + 1 - tr)}"
    if tr:
        d += f"A{num(tr)} {num(tr)} 0 0 1 {num(x + 1)} {num(y + tr)}"
    d += f"V{num(y + 1 - br)}"
    if br:
        d += f"A{num(br)} {num(br)} 0 0 1 {num(x + 1 - br)} {num(y + 1)}"
    d += f"H{num(x + bl)}"
    if bl:
        d += f"A{num(bl)} {num(bl)} 0 0 1 {num(x)} {num(y + 1 - bl)}"
    d += f"V{num(y + tl)}"
    if tl:
        d += f"A{num(tl)} {num(tl)} 0 0 1 {num(x + tl)} {num(y)}"
    return d + "Z"


def fillet(cx, cy, dx, dy, r):
    """Concave fill for the inside corner at (cx, cy); (dx, dy) points into the light cell.

    Always wound the same way as the modules, so anti-aliasing doesn't leave seams where they meet.
    """
    h = f"{num(cx + dx * r)} {num(cy)}"
    v = f"{num(cx)} {num(cy + dy * r)}"
    first, last = (h, v) if dx * dy > 0 else (v, h)
    return f"M{num(cx)} {num(cy)}L{first}A{num(r)} {num(r)} 0 0 0 {last}Z"


def render_svg(code):
    qr = segno.make_qr(code["data"], error="h", boost_error=False)
    matrix = [[bool(v) for v in row] for row in qr.matrix]
    n = len(matrix)
    size = n + 2 * QUIET
    zone = (n - LOGO_ZONE) // 2

    def is_eye(x, y):
        return (x < 8 and y < 8) or (x >= n - 8 and y < 8) or (x < 8 and y >= n - 8)

    def is_logo(x, y):
        return zone <= x < zone + LOGO_ZONE and zone <= y < zone + LOGO_ZONE

    def dark(x, y):
        return 0 <= x < n and 0 <= y < n and matrix[y][x] and not is_eye(x, y) and not is_logo(x, y)

    parts = []
    for y in range(n):
        for x in range(n):
            px, py = x + QUIET, y + QUIET
            up, down, left, right = dark(x, y - 1), dark(x, y + 1), dark(x - 1, y), dark(x + 1, y)
            if dark(x, y):
                parts.append(module(px, py,
                                    CORNER * (not up and not left), CORNER * (not up and not right),
                                    CORNER * (not down and not right), CORNER * (not down and not left)))
                continue
            for cx, cy, dx, dy, a, b, diag in (
                (px, py, 1, 1, up, left, dark(x - 1, y - 1)),
                (px + 1, py, -1, 1, up, right, dark(x + 1, y - 1)),
                (px + 1, py + 1, -1, -1, down, right, dark(x + 1, y + 1)),
                (px, py + 1, 1, -1, down, left, dark(x - 1, y + 1)),
            ):
                if a and b and diag:
                    parts.append(fillet(cx, cy, dx, dy, FILLET))

    ro, ri, rc = EYE_RADII
    eyes = "".join(
        rounded_rect(ex + QUIET, ey + QUIET, 7, 7, ro)
        + rounded_rect(ex + QUIET + 1, ey + QUIET + 1, 5, 5, ri)
        + rounded_rect(ex + QUIET + 2, ey + QUIET + 2, 3, 3, rc)
        for ex, ey in ((0, 0), (n - 7, 0), (0, n - 7))
    )

    lw, lh, ld = code["logo"]
    scale = code["logo_size"] / max(lw, lh)
    lx, ly = size / 2 - lw * scale / 2, size / 2 - lh * scale / 2
    px_size = size * MODULE_PX
    return px_size, (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{px_size}" height="{px_size}">'
        f'<rect width="{size}" height="{size}" fill="#fff"/>'
        f'<path fill="{INK}" d="{"".join(parts)}"/>'
        f'<path fill="{code["eye"]}" fill-rule="evenodd" d="{eyes}"/>'
        f'<path fill="{code["logo_color"]}" transform="translate({num(lx)} {num(ly)}) scale({num(scale)})" d="{ld}"/>'
        f"</svg>"
    )


def find_browser():
    candidates = [
        os.environ.get("CHROME"),
        *(shutil.which(b) for b in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge")),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    return next((c for c in candidates if c and Path(c).exists()), None)


def rasterize(browser, svg_path, png_path, px, profile):
    subprocess.run(
        [browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
         f"--user-data-dir={profile}", "--force-device-scale-factor=1",
         f"--window-size={px},{px}", f"--screenshot={png_path}", svg_path.as_uri()],
        check=True, capture_output=True,
    )
    try:
        from PIL import Image
    except ImportError:
        return
    # A small palette keeps the anti-aliasing and cuts the file to under half.
    with Image.open(png_path) as im:
        im = im.convert("RGB").quantize(64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    im.save(png_path, optimize=True)


def main():
    browser = find_browser()
    if not browser:
        sys.exit("Chrome/Edge not found; set CHROME=/path/to/browser")
    ASSETS.mkdir(exist_ok=True)
    # Chrome can hold its temp profile open for a moment after exiting, hence ignore_cleanup_errors.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp = Path(tmp)
        for code in CODES:
            px, svg = render_svg(code)
            svg_path = tmp / (code["file"] + ".svg")
            svg_path.write_text(svg, encoding="utf-8")
            png_path = ASSETS / code["file"]
            rasterize(browser, svg_path, png_path, px, tmp / "profile")
            print(f"wrote {png_path.relative_to(ROOT)} ({px}x{px})")


if __name__ == "__main__":
    main()
