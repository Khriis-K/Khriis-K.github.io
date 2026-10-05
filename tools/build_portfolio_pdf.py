"""Build Christopher-Kuizon-Portfolio.pdf from portfolio-print.html.

1. Renders print stills into assets/print/: the hero frame clear and at fog
   severity 0.60 (with detector boxes from assets/hero.json), and one frame
   from each demo GIF.
2. Prints portfolio-print.html to PDF with headless Edge or Chrome.

Run from anywhere:  python tools/build_portfolio_pdf.py
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ASSETS / "print"
PDF = ROOT / "Christopher-Kuizon-Portfolio.pdf"

SCALE = 2  # draw the hero at 2x so boxes stay crisp in print
FOG_STEP = 12  # severity 0.60, the step the site's caption quotes
EDGE_FRAME = 17  # side-by-side clean vs degraded with the match table
COUNCIL_FRAME = 48  # counselors arranged around the dilemma

ORANGE = (240, 131, 74)


def hero(step_index, name):
    h = json.loads((ASSETS / "hero.json").read_text(encoding="utf-8"))
    th = h["thresholds"]["outcome"]
    step = h["steps"][step_index]
    img = Image.open(ASSETS / "hero-clean.jpg").convert("RGB")
    img = img.resize((img.width * SCALE, img.height * SCALE), Image.LANCZOS)
    # Same fog as the site: an rgb(204,204,204) layer at opacity 1 - t.
    fog = Image.new("RGB", img.size, (204, 204, 204))
    img = Image.blend(img, fog, 1 - step["transmission"])
    d = ImageDraw.Draw(img, "RGBA")
    for g in h["ground_truth"]:
        d.rectangle([v * SCALE for v in g["box"]], outline=(255, 255, 255, 153), width=2)
    for det in step["detections"]:
        if det["score"] >= th:
            d.rectangle([v * SCALE for v in det["box"]], outline=ORANGE, width=4)
    img.save(OUT / name, quality=88)
    return sum(det["score"] >= th for det in step["detections"])


def gif_frame(src, index, name):
    im = Image.open(ASSETS / src)
    im.seek(index)
    im.convert("RGB").save(OUT / name, quality=88)


def browser():
    candidates = [
        os.environ.get("CHROME"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        shutil.which("chrome"),
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("msedge"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    raise SystemExit("No Chrome or Edge found; set CHROME to its path.")


def main():
    OUT.mkdir(exist_ok=True)
    clear = hero(0, "hero-clear.jpg")
    fogged = hero(FOG_STEP, "hero-fog.jpg")
    print(f"hero: {clear} detections clear, {fogged} at severity 0.60")
    gif_frame("edge-demo.gif", EDGE_FRAME, "edge.jpg")
    gif_frame("council-demo.gif", COUNCIL_FRAME, "council.jpg")

    subprocess.run(
        [
            browser(),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--virtual-time-budget=10000",  # let the web fonts load
            f"--print-to-pdf={PDF}",
            (ROOT / "portfolio-print.html").as_uri(),
        ],
        check=True,
    )
    print(f"wrote {PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
