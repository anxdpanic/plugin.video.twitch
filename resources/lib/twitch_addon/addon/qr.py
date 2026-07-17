# -*- coding: utf-8 -*-
"""

    Copyright (C) 2024-2025 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.

    Dependency-free QR code -> PNG rendering used by the device-code login flow.
    Uses the vendored Project Nayuki QR generator (MIT) for the module matrix and
    a tiny zlib-based PNG writer so no binary image library (PIL/Pillow) is needed.
"""

import struct
import zlib

from .vendor.qrcodegen import QrCode


def _write_grayscale_png(file_path, width, height, rows):
    """Write an 8-bit grayscale PNG. ``rows`` is an iterable of ``width``-length
    bytes objects (one byte per pixel, 0=black .. 255=white)."""

    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    raw = bytearray()
    for row in rows:
        raw.append(0)  # filter type 0 (None) for each scanline
        raw.extend(row)

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0)  # 8-bit grayscale
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')

    with open(file_path, 'wb') as handle:
        handle.write(png)
    return file_path


def generate_qr_png(data, file_path, scale=8, border=4, ecc=None):
    """Render ``data`` as a QR code PNG at ``file_path``.

    :param scale: pixels per QR module
    :param border: quiet-zone width in modules (the spec requires >= 4)
    :returns: ``file_path`` on success
    """
    if ecc is None:
        ecc = QrCode.Ecc.MEDIUM
    qr = QrCode.encode_text(data, ecc)
    size = qr.get_size()
    total = size + 2 * border
    width = height = total * scale

    rows = []
    for ty in range(total):
        line = bytearray(width)
        for tx in range(total):
            mx = tx - border
            my = ty - border
            dark = (0 <= mx < size) and (0 <= my < size) and qr.get_module(mx, my)
            value = 0 if dark else 255
            base = tx * scale
            for sx in range(scale):
                line[base + sx] = value
        packed = bytes(line)
        for _ in range(scale):
            rows.append(packed)

    return _write_grayscale_png(file_path, width, height, rows)


def generate_solid_png(file_path, width, height, value=18):
    """Write a solid grayscale rectangle, used as a backdrop panel behind the QR."""
    row = bytes([value]) * width
    return _write_grayscale_png(file_path, width, height, (row for _ in range(height)))
