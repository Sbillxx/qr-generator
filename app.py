import io
import os
import re

import qrcode
import qrcode.constants
import qrcode.exceptions
from flask import Flask, Response, abort, render_template, request, send_file
from PIL import Image

app = Flask(__name__)

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
MAX_TEXT_LENGTH = 1000
MIN_SIZE, MAX_SIZE = 128, 1200


@app.errorhandler(400)
def bad_request(error):
    # Plain text so the page can show the message directly.
    return Response(error.description, status=400, mimetype="text/plain")


def read_options():
    text = request.args.get("text", "").strip()
    if not text:
        abort(400, "Isi teks atau URL dulu.")
    if len(text) > MAX_TEXT_LENGTH:
        abort(400, f"Teks terlalu panjang (maksimal {MAX_TEXT_LENGTH} karakter).")

    try:
        size = int(request.args.get("size", 400))
    except ValueError:
        abort(400, "Ukuran harus berupa angka.")
    size = max(MIN_SIZE, min(MAX_SIZE, size))

    fg = request.args.get("fg", "#000000")
    bg = request.args.get("bg", "#ffffff")
    if not (HEX_COLOR.match(fg) and HEX_COLOR.match(bg)):
        abort(400, "Format warna harus seperti #1a2b3c.")

    transparent = request.args.get("transparent") == "1"
    return text, size, fg, bg, transparent


def make_matrix(text):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=4,  # quiet zone, included in the matrix
    )
    qr.add_data(text)
    try:
        qr.make(fit=True)
    except qrcode.exceptions.DataOverflowError:
        abort(400, "Teks terlalu panjang untuk dijadikan QR code.")
    return qr.get_matrix()


def hex_to_rgb(value):
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))


def render_png(matrix, size, fg, bg, transparent):
    n = len(matrix)
    size = max(size, n)  # never smaller than 1 pixel per module
    fg_px = (*hex_to_rgb(fg), 255)
    bg_px = (*hex_to_rgb(bg), 0 if transparent else 255)

    small = Image.new("RGBA", (n, n))
    small.putdata([fg_px if cell else bg_px for row in matrix for cell in row])

    # Whole-pixel scaling keeps every module sharp; leftover space is padding.
    scale = size // n
    big = small.resize((n * scale, n * scale), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (size, size), bg_px)
    offset = (size - n * scale) // 2
    canvas.paste(big, (offset, offset))

    buffer = io.BytesIO()
    canvas.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def render_svg(matrix, size, fg, bg, transparent):
    n = len(matrix)
    runs = []
    for y, row in enumerate(matrix):
        x = 0
        while x < n:
            if row[x]:
                start = x
                while x < n and row[x]:
                    x += 1
                runs.append(f"M{start} {y}h{x - start}v1h-{x - start}z")
            else:
                x += 1

    background = "" if transparent else f'<rect width="{n}" height="{n}" fill="{bg}"/>'
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" '
        f'width="{size}" height="{size}" shape-rendering="crispEdges">'
        f'{background}<path fill="{fg}" d="{"".join(runs)}"/></svg>'
    )
    return io.BytesIO(svg.encode("utf-8"))


FORMATS = {
    "png": (render_png, "image/png"),
    "svg": (render_svg, "image/svg+xml"),
}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/qr/<fmt>")
def qr(fmt):
    if fmt not in FORMATS:
        abort(404)
    text, size, fg, bg, transparent = read_options()
    render, mimetype = FORMATS[fmt]
    buffer = render(make_matrix(text), size, fg, bg, transparent)
    return send_file(
        buffer,
        mimetype=mimetype,
        as_attachment=request.args.get("download") == "1",
        download_name=f"qr-code.{fmt}",
    )


@app.get("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True)
