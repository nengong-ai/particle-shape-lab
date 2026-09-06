"""Trace PNG silhouettes along exact pixel boundaries. No smoothing or renderer."""
from collections import defaultdict
import hashlib
import math
from pathlib import Path

import numpy as np
from PIL import Image

def decode_mask(path, foreground='auto', threshold=128):
    if foreground not in {'auto', 'alpha', 'dark', 'light'}:
        raise ValueError('Unknown foreground mode.')
    if not 1 <= threshold <= 254:
        raise ValueError('Threshold must be an integer from 1 to 254.')
    with Image.open(path) as image:
        if image.format != 'PNG':
            raise ValueError('Input must be PNG.')
        if getattr(image, 'n_frames', 1) != 1:
            raise ValueError('Animated PNG is unsupported; provide one static frame.')
        if image.width * image.height > 4_194_304 or max(image.size) > 4096:
            raise ValueError('PNG exceeds 4 megapixels or 4096 px on one side; provide a smaller silhouette.')
        with Path(path).open('rb') as source:
            header = source.read(26)
        bit_depth, color_type = header[24], header[25]
        input_mode = image.mode
        if bit_depth == 16:
            if color_type != 0:
                raise ValueError('16-bit PNG is supported for grayscale only; convert other 16-bit formats to 8-bit explicitly.')
            values = np.array(image).astype(np.uint32)
            # Pillow's I;16 -> RGBA conversion clamps instead of rescaling.
            # Normalize the full 0..65535 range to the documented 0..255 threshold scale.
            gray8 = ((values + 128) // 257).astype(np.uint8)
            alpha8 = np.full(gray8.shape, 255, dtype=np.uint8)
            transparent_value = image.info.get('transparency')
            if transparent_value is not None:
                alpha8[values == transparent_value] = 0
            rgba = np.stack((gray8, gray8, gray8, alpha8), axis=-1)
        else:
            rgba = np.array(image.convert('RGBA'))
    alpha = rgba[:, :, 3]
    mode = foreground
    transparent = bool(np.any(alpha < 255))
    if mode == 'auto' and transparent:
        mode = 'alpha'
    if mode == 'alpha':
        if not transparent:
            raise ValueError('Alpha mode needs transparency; otherwise the whole canvas would become foreground.')
        mask = alpha >= threshold
    else:
        rgb = rgba[:, :, :3].astype(np.int16)
        if transparent:
            raise ValueError('For a transparent PNG use alpha mode; dark/light mode expects an opaque grayscale image.')
        if np.any(rgb.max(axis=2) - rgb.min(axis=2) > 8):
            raise ValueError('Opaque PNG must be black/white or grayscale; colored images need an explicit silhouette.')
        gray = rgb[:, :, 0]
        if mode == 'auto':
            border = np.concatenate((gray[0, :], gray[-1, :], gray[1:-1, 0], gray[1:-1, -1]))
            light_fraction = float(np.mean(border >= threshold))
            if light_fraction >= 0.9:
                mode = 'dark'
            elif light_fraction <= 0.1:
                mode = 'light'
            else:
                raise ValueError('Border polarity is ambiguous; choose --foreground dark or light after viewing the PNG.')
        mask = gray < threshold if mode == 'dark' else gray >= threshold
    if not np.any(mask):
        raise ValueError('The selected foreground is empty at this threshold.')
    if np.all(mask):
        raise ValueError('The selected foreground fills the entire canvas; check the threshold/polarity.')
    ys, xs = np.nonzero(mask)
    crop = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    mask = mask[crop[1]:crop[3], crop[0]:crop[2]].copy()
    return mask, {'inputMode': input_mode, 'inputBitDepth': bit_depth,
                  'thresholdScale': '0..255; 16-bit grayscale is normalized over its full range',
                  'originalSize': [int(rgba.shape[1]), int(rgba.shape[0])],
                  'requestedForeground': foreground, 'resolvedForeground': mode,
                  'threshold': threshold, 'cropBox': crop, 'foregroundPixels': int(mask.sum())}


def contour_loops(mask):
    # Directed pixel-cell boundaries keep foreground on the right. Holes and
    # disconnected components remain separate closed loops, including corner contact.
    padded = np.pad(mask, 1)
    top = mask & ~padded[:-2, 1:-1]
    right = mask & ~padded[1:-1, 2:]
    bottom = mask & ~padded[2:, 1:-1]
    left = mask & ~padded[1:-1, :-2]
    edge_count = sum(int(a.sum()) for a in (top, right, bottom, left))
    if edge_count > 100_000:
        raise ValueError('Too much contour detail/noise; simplify the PNG instead of silently discarding components.')
    edges = set()
    for direction, boundary in enumerate((top, right, bottom, left)):
        for y, x in zip(*np.nonzero(boundary)):
            x, y = int(x), int(y)
            start, end = (((x, y), (x + 1, y)), ((x + 1, y), (x + 1, y + 1)),
                          ((x + 1, y + 1), (x, y + 1)), ((x, y + 1), (x, y)))[direction]
            edges.add((start, end))
    outgoing = defaultdict(set)
    for a, b in edges:
        outgoing[a].add(b)
    loops = []
    directions = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}
    priorities = {1: 0, 0: 1, 3: 2, 2: 3}
    while edges:
        first = min(edges)
        start, current = first
        previous = start
        points = [start]
        edges.remove(first)
        outgoing[start].remove(current)
        while current != start:
            points.append(current)
            candidates = outgoing[current]
            if not candidates:
                raise ValueError('Contour did not close; input trace aborted.')
            incoming = directions[(current[0] - previous[0], current[1] - previous[1])]
            nxt = min(candidates, key=lambda b: priorities[(directions[(b[0] - current[0], b[1] - current[1])] - incoming) % 4])
            edges.remove((current, nxt))
            candidates.remove(nxt)
            previous, current = current, nxt
        # Remove only collinear vertices: no smoothing, area filter or shape guessing.
        simplified = []
        for index, point in enumerate(points):
            before, after = points[index - 1], points[(index + 1) % len(points)]
            if (point[0] - before[0]) * (after[1] - point[1]) != (point[1] - before[1]) * (after[0] - point[0]):
                simplified.append(point)
        if len(simplified) < 4:
            raise ValueError('Degenerate contour.')
        loops.append(simplified)
        if len(loops) > 64:
            raise ValueError('More than 64 boundaries; simplify image noise explicitly.')
    if sum(map(len, loops)) > 6000:
        raise ValueError('More than 6000 contour vertices; provide a simpler or smaller PNG.')
    return loops


def rasterize_centers(loops, width, height):
    """Round-trip evenodd polygons at original pixel centers, including holes."""
    result = np.zeros((height, width), dtype=bool)
    segments = [(a, b) for loop in loops for a, b in zip(loop, loop[1:] + loop[:1]) if a[1] != b[1]]
    for y in range(height):
        scan = y + 0.5
        crossings = sorted(a[0] + (scan - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
                           for a, b in segments if min(a[1], b[1]) <= scan < max(a[1], b[1]))
        if len(crossings) % 2:
            raise ValueError('Odd contour crossing count; trace aborted.')
        for left, right in zip(crossings[::2], crossings[1::2]):
            begin, end = math.ceil(left - 0.5), math.ceil(right - 0.5)
            result[y, max(0, begin):min(width, end)] = True
    return result


def trace_png(path, foreground='auto', threshold=128):
    mask, metadata = decode_mask(path, foreground, threshold)
    loops = contour_loops(mask)
    height, width = mask.shape
    if not np.array_equal(mask, rasterize_centers(loops, width, height)):
        raise ValueError('Contour round-trip differs from thresholded input; nothing was exported.')
    areas = [sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(loop, loop[1:] + loop[:1])) / 2 for loop in loops]
    paths = ['M ' + ' L '.join(f'{x} {y}' for x, y in loop) + ' Z' for loop in loops]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="#ffffff" fill-rule="evenodd">\n'
           + '  <path d="' + ' '.join(paths) + '"/>\n</svg>\n').encode()
    metadata.update({'croppedSize': [width, height], 'components': sum(a > 0 for a in areas),
                     'holes': sum(a < 0 for a in areas), 'contours': len(loops),
                     'vertices': sum(map(len, loops)), 'pixelRoundTripExact': True,
                     'simplification': 'Collinear vertices only; no smoothing, component deletion or rescaling.',
                     'svgSha256': hashlib.sha256(svg).hexdigest(),
                     'inputSha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()})
    return svg, metadata
