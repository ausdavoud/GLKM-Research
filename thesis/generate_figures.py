from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).parent / "Figures"
FONT = Path(__file__).parent / "Fonts" / "Times New Roman.ttf"


def font(size, bold=False):
    return ImageFont.truetype(str(FONT), size)


def save(img, name):
    img.save(OUT / name, quality=95)


def rectangle_example():
    img = Image.new("RGB", (1600, 760), "white")
    d = ImageDraw.Draw(img)
    blue, red, ink, gray = "#1976b9", "#dc4a4a", "#17212b", "#9aa5af"
    panels = [(90, "Possible MacQueen limit", "horizontal split"), (850, "Lower-SSE partition", "vertical split")]
    for x0, title, subtitle in panels:
        d.text((x0 + 250, 40), title, fill=ink, font=font(38), anchor="ma")
        d.text((x0 + 250, 88), subtitle, fill=gray, font=font(27), anchor="ma")
        box = (x0 + 60, 165, x0 + 520, 555)
        d.rectangle(box, outline=ink, width=5)
        pts = [(box[0], box[1]), (box[0], box[3]), (box[2], box[1]), (box[2], box[3])]
        for i, p in enumerate(pts, 1):
            d.ellipse((p[0] - 14, p[1] - 14, p[0] + 14, p[1] + 14), fill=ink)
            d.text((p[0] + (24 if p[0] == box[0] else -24), p[1] + (-38 if p[1] == box[1] else 22)), str(i), fill=ink, font=font(26), anchor="mm")
        if x0 < 500:
            d.line((box[0], (box[1] + box[3]) / 2, box[2], (box[1] + box[3]) / 2), fill=gray, width=4)
            centers = [((box[0] + box[2]) / 2, box[1], blue), ((box[0] + box[2]) / 2, box[3], red)]
        else:
            d.line(((box[0] + box[2]) / 2, box[1], (box[0] + box[2]) / 2, box[3]), fill=gray, width=4)
            centers = [(box[0], (box[1] + box[3]) / 2, blue), (box[2], (box[1] + box[3]) / 2, red)]
        for cx, cy, color in centers:
            d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=color, outline="white", width=4)
            d.line((cx - 12, cy, cx + 12, cy), fill="white", width=4)
            d.line((cx, cy - 12, cx, cy + 12), fill="white", width=4)
    save(img, "macqueen_rectangle.png")


def line_chart(draw, box, xs, ys, title, color, marker_x=None):
    x0, y0, x1, y1 = box
    draw.text(((x0 + x1) / 2, y0 - 60), title, fill="#17212b", font=font(34), anchor="ma")
    draw.line((x0, y0, x0, y1, x1, y1), fill="#17212b", width=4)
    ymin, ymax = min(ys), max(ys)
    if ymin == ymax:
        ymin, ymax = ymin - 1, ymax + 1
    pts = []
    for x, y in zip(xs, ys):
        px = x0 + (x - min(xs)) / (max(xs) - min(xs)) * (x1 - x0)
        py = y1 - (y - ymin) / (ymax - ymin) * (y1 - y0)
        pts.append((px, py))
        draw.ellipse((px - 7, py - 7, px + 7, py + 7), fill=color)
    draw.line(pts, fill=color, width=6)
    for x in xs:
        px = x0 + (x - min(xs)) / (max(xs) - min(xs)) * (x1 - x0)
        draw.text((px, y1 + 18), str(x), fill="#65717d", font=font(22), anchor="ma")
    if marker_x is not None:
        px = x0 + (marker_x - min(xs)) / (max(xs) - min(xs)) * (x1 - x0)
        draw.line((px, y0, px, y1), fill="#dc4a4a", width=4)
        draw.text((px + 10, y0 + 12), f"estimated k={marker_x}", fill="#dc4a4a", font=font(22))


def elbow_results():
    img = Image.new("RGB", (1800, 760), "white")
    d = ImageDraw.Draw(img)
    xs = list(range(2, 11))
    line_chart(d, (100, 155, 820, 610), xs, [100936.0647] * 9, "D1: disconnected graph (186 components)", "#1976b9")
    line_chart(
        d,
        (980, 155, 1700, 610),
        xs,
        [25857500, 25796800, 25738500, 25680800, 25625900, 25571700, 25517600, 25464200, 25413300],
        "Gisette: almost linear objective decrease",
        "#1976b9",
        5,
    )
    d.text((900, 710), "number of requested clusters (k)", fill="#17212b", font=font(28), anchor="mm")
    save(img, "elbow_results.png")


def bars(draw, box, values, labels, title, colors, ymax):
    x0, y0, x1, y1 = box
    draw.text(((x0 + x1) / 2, y0 - 55), title, fill="#17212b", font=font(34), anchor="ma")
    draw.line((x0, y0, x0, y1, x1, y1), fill="#17212b", width=4)
    width = (x1 - x0) / len(values)
    for i, (v, label) in enumerate(zip(values, labels)):
        left = x0 + i * width + width * 0.2
        right = x0 + (i + 1) * width - width * 0.2
        top = y1 - v / ymax * (y1 - y0)
        draw.rectangle((left, top, right, y1), fill=colors[i])
        draw.text(((left + right) / 2, top - 10), f"{v:.3g}", fill="#17212b", font=font(22), anchor="ms")
        draw.text(((left + right) / 2, y1 + 18), label, fill="#65717d", font=font(21), anchor="ma")


def kpp_results():
    img = Image.new("RGB", (1800, 820), "white")
    d = ImageDraw.Draw(img)
    labels = ["raw", "4k", "10k", "25k", "100k"]
    palette = ["#17212b", "#6b89a4", "#597f9f", "#477696", "#2f698b"]
    bars(d, (100, 165, 820, 665), [1.33, 2.783, 3.278, 3.732, 10.87], labels, "Total runtime (seconds)", palette, 12)
    x0, y0, x1, y1 = 980, 165, 1700, 665
    d.text(((x0 + x1) / 2, y0 - 55), "External clustering quality", fill="#17212b", font=font(34), anchor="ma")
    d.line((x0, y0, x0, y1, x1, y1), fill="#17212b", width=4)
    acc, nmi = [0.795, 0.577, 0.748, 0.588, 0.760], [0.358, 0.033, 0.210, 0.054, 0.269]
    width = (x1 - x0) / len(labels)
    for i, label in enumerate(labels):
        cx = x0 + (i + 0.5) * width
        for value, dx, color in [(acc[i], -22, "#1976b9"), (nmi[i], 22, "#dc4a4a")]:
            top = y1 - value * (y1 - y0)
            d.rectangle((cx + dx - 18, top, cx + dx + 18, y1), fill=color)
        d.text((cx, y1 + 18), label, fill="#65717d", font=font(21), anchor="ma")
    d.rectangle((1190, 716, 1220, 746), fill="#1976b9")
    d.text((1235, 731), "ACC", fill="#17212b", font=font(23), anchor="lm")
    d.rectangle((1350, 716, 1380, 746), fill="#dc4a4a")
    d.text((1395, 731), "NMI", fill="#17212b", font=font(23), anchor="lm")
    save(img, "kpp_results.png")


rectangle_example()
elbow_results()
kpp_results()
