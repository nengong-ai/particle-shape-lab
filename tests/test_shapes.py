"""Geometry and trust-boundary tests. All input fixtures are authored here."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from shape import convert
from svg_input import parse_svg
from png_input import decode_mask, contour_loops, rasterize_centers, trace_png


class TemporaryCase(unittest.TestCase):
    def setUp(self):
        base = os.environ.get('TEST_TMPDIR')
        if base:
            Path(base).mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='shape-test-', dir=base)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def svg(self, body='<path d="M0 0H4V4H0Z"/>'):
        path = self.root / 'input.svg'
        path.write_text('<svg viewBox="0 0 12 8">' + body + '</svg>', encoding='utf-8')
        return path

    def png(self, values, name='input.png'):
        path = self.root / name
        Image.fromarray(values).save(path)
        return path

    def symlink(self, source, link):
        try:
            link.symlink_to(source, target_is_directory=source.is_dir())
        except (OSError, NotImplementedError) as error:
            self.skipTest('Symlink creation unavailable on this runner: ' + str(error))


class SvgTests(TemporaryCase):
    def test_compound_hole_and_disconnected_component_survive(self):
        source = self.svg('<g fill-rule="evenodd"><path d="M0 0H6V6H0Z M2 2H4V4H2Z"/>'
                          '<path d="M9 1H11V3H9Z"/></g>')
        geometry, normalized = parse_svg(source.read_bytes())
        self.assertEqual(geometry['fillRules'], ['evenodd', 'evenodd'])
        self.assertEqual(len(geometry['paths']), 2)
        self.assertEqual(geometry['paths'][0].count('M'), 2)
        self.assertEqual(geometry, parse_svg(normalized)[0])

    def test_reject_executable_and_external_svg(self):
        bodies = [
            '<script>alert(1)</script>',
            '<path onload="alert(1)" d="M0 0H4V4Z"/>',
            '<g onclick="alert(1)"><path d="M0 0H4V4Z"/></g>',
            '<image href="https://invalid.example/image.png"/>',
            '<use href="#foreign"/>',
            '<foreignObject><div>payload</div></foreignObject>',
            '<path style="fill:url(https://invalid.example/)" d="M0 0H4V4Z"/>',
            '<path fill="url(#paint)" d="M0 0H4V4Z"/>',
            '<title onload="alert(1)">Title</title><path d="M0 0H4V4Z"/>',
            '<desc><script>alert(1)</script></desc><path d="M0 0H4V4Z"/>',
        ]
        for body in bodies:
            with self.subTest(body=body), self.assertRaises((ValueError, ET.ParseError)):
                parse_svg(self.svg(body).read_bytes())

    def test_reject_doctype_nonfinite_open_and_bad_arc(self):
        invalid = [
            b'<!DOCTYPE svg [<!ENTITY x "x">]><svg viewBox="0 0 4 4"/>',
            b'<svg viewBox="0 0 1e999 4"><path d="M0 0H4V4Z"/></svg>',
            b'<svg viewBox="0 0 4 4"><path d="M0 0L2 2"/></svg>',
            b'<svg viewBox="0 0 4 4"><path d="M0 0A1 1 0 2 0 2 2Z"/></svg>',
        ]
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises((ValueError, ET.ParseError)):
                parse_svg(raw)

    def test_convert_preserves_original_and_hashes(self):
        source = self.svg()
        raw = source.read_bytes()
        manifest = convert(source, self.root / 'out', title='Original test shape')
        out = self.root / 'out'
        self.assertEqual((out / 'original.svg').read_bytes(), raw)
        self.assertEqual(manifest['inputSha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(manifest['normalizedSha256'], hashlib.sha256((out / 'normalized.svg').read_bytes()).hexdigest())
        self.assertFalse(manifest['browserVerified'])
        self.assertEqual(json.loads((out / 'shape.json').read_text())['geometry']['label'], 'Original test shape')

    def test_empty_output_accepted_nonempty_and_source_parent_preserved(self):
        source = self.svg()
        out = self.root / 'out'
        out.mkdir()
        convert(source, out)
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with self.assertRaises(ValueError):
            convert(source, out)
        self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})
        with self.assertRaises(ValueError):
            convert(source, self.root)
        self.assertTrue(source.exists())

    def test_invalid_input_does_not_populate_empty_output(self):
        out = self.root / 'out'
        out.mkdir()
        with self.assertRaises(ValueError):
            convert(self.svg('<script/>'), out)
        self.assertEqual(list(out.iterdir()), [])

    def test_output_symlink_rejected(self):
        source = self.svg()
        target = self.root / 'target'
        target.mkdir()
        link = self.root / 'alias'
        self.symlink(target, link)
        with self.assertRaises(ValueError):
            convert(source, link / 'out')
        self.assertEqual(list(target.iterdir()), [])


class PngTests(TemporaryCase):
    def test_alpha_preserves_hole_disconnected_pixels_and_original(self):
        rgba = np.zeros((9, 13, 4), dtype=np.uint8)
        rgba[1:8, 1:8, :3] = (220, 30, 60)
        rgba[1:8, 1:8, 3] = 255
        rgba[3:6, 3:6, 3] = 0
        rgba[2, 11] = (10, 240, 50, 255)
        source = self.png(rgba)
        svg, meta = trace_png(source)
        self.assertEqual((meta['components'], meta['holes']), (2, 1))
        self.assertEqual(meta['foregroundPixels'], 41)
        self.assertTrue(meta['pixelRoundTripExact'])
        self.assertEqual(meta['resolvedForeground'], 'alpha')
        self.assertEqual(parse_svg(svg)[0]['fillRules'], ['evenodd'])
        convert(source, self.root / 'out')
        self.assertEqual((self.root / 'out/original.png').read_bytes(), source.read_bytes())

    def test_dark_and_inverted_auto_have_identical_geometry(self):
        pixels = np.full((7, 9), 255, dtype=np.uint8)
        pixels[2:5, 2:7] = 0
        pixels[3, 4] = 255
        dark, dark_meta = decode_mask(self.png(pixels))
        light, light_meta = decode_mask(self.png(255 - pixels, 'inverted.png'))
        np.testing.assert_array_equal(dark, light)
        self.assertEqual(dark_meta['resolvedForeground'], 'dark')
        self.assertEqual(light_meta['resolvedForeground'], 'light')
        self.assertEqual(dark_meta['cropBox'], [2, 2, 7, 5])

    def test_16bit_grayscale_uses_full_range(self):
        pixels = np.full((5, 5), 65535, dtype=np.uint16)
        pixels[1:4, 1:4] = 30000  # 117 at 8-bit, not Pillow's clamped 255.
        pixels[2, 2] = 40000
        mask, meta = decode_mask(self.png(pixels), 'dark', 128)
        self.assertEqual(meta['inputBitDepth'], 16)
        self.assertEqual(int(mask.sum()), 8)
        self.assertFalse(mask[1, 1])

    def test_reject_opaque_alpha_colored_and_empty_inputs(self):
        opaque = self.png(np.full((4, 4), 255, dtype=np.uint8))
        for mode in ['alpha', 'dark', 'light']:
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                decode_mask(opaque, mode)
        colored = np.zeros((4, 4, 3), dtype=np.uint8)
        colored[:, :] = (220, 0, 50)
        with self.assertRaises(ValueError):
            decode_mask(self.png(colored), 'dark')

    def test_exact_contour_roundtrip_holes_corners_and_seeded_masks(self):
        ring = np.ones((5, 5), dtype=bool)
        ring[1:4, 1:4] = False
        masks = [ring, np.eye(5, dtype=bool), np.array([[True, False, True]])]
        random = np.random.default_rng(42017)
        masks.extend(random.random((6, 7)) < .4 for _ in range(80))
        for number, mask in enumerate(masks):
            with self.subTest(number=number):
                loops = contour_loops(mask)
                actual = rasterize_centers(loops, mask.shape[1], mask.shape[0])
                np.testing.assert_array_equal(actual, mask)


if __name__ == '__main__':
    unittest.main()
