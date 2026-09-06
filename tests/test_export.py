"""Export boundary tests using original, non-rendering runtime stubs only."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_fixture import NOTICE, SVG, write_runtime
from test_shapes import ROOT, TemporaryCase
from export import export_project
from shape import convert


class ExportTests(TemporaryCase):
    def setUp(self):
        super().setUp()
        self.runtime = self.root / 'runtime'
        self.contract = write_runtime(self.runtime)
        self.source = self.root / 'source.svg'
        self.source.write_bytes(SVG)
        self.shape_dir = self.root / 'shape'
        convert(self.source, self.shape_dir, title='Own <shape> & text')
        self.shape = self.shape_dir / 'shape.json'
        self.out = self.root / 'export'

    def export(self, destination=None, runtime=None):
        return export_project(runtime or self.runtime, self.shape,
                              destination or self.out, contracts=self.contract)

    def test_export_preserves_original_and_external_notice(self):
        report = self.export()
        self.assertEqual((self.out / 'input/original.svg').read_bytes(), SVG)
        self.assertEqual((self.out / 'input/manifest.json').read_bytes(),
                         (self.shape_dir / 'manifest.json').read_bytes())
        self.assertEqual((self.out / 'runtime-notices/LICENSE').read_bytes(), NOTICE)
        self.assertEqual((self.out / 'src/particles/core/README.md').read_bytes(), NOTICE)
        self.assertFalse(report['browserVerified'])
        self.assertTrue(report['originalInputPreserved'])
        self.assertIn('Own &lt;shape&gt; &amp; text', (self.out / 'index.html').read_text())
        self.assertFalse((self.out / 'node_modules').exists())
        self.assertEqual(report['runtimeContract'], 'original-test-stub')
        package = json.loads((self.out / 'package.json').read_text())
        lock = json.loads((self.out / 'package-lock.json').read_text())
        self.assertNotIn('license', package)
        self.assertNotIn('license', lock['packages'][''])
        self.assertEqual(package['name'], lock['packages']['']['name'])

    def test_runtime_tampering_rejected_before_output(self):
        path = self.runtime / 'src/particles/engine.ts'
        path.write_bytes(path.read_bytes() + b'// tampered\n')
        with self.assertRaisesRegex(ValueError, 'Runtime differs'):
            self.export()
        self.assertFalse(self.out.exists())

    def test_uncontracted_runtime_files_are_not_copied(self):
        (self.runtime / 'src/private-unlisted.ts').write_text('unlisted', encoding='utf-8')
        (self.runtime / 'private-key.txt').write_text('fake test marker', encoding='utf-8')
        self.export()
        self.assertFalse((self.out / 'src/private-unlisted.ts').exists())
        self.assertFalse((self.out / 'runtime-notices/private-key.txt').exists())

    def test_runtime_file_symlink_rejected_even_when_bytes_match(self):
        path = self.runtime / 'src/particles/engine.ts'
        outside = self.root / 'identical-engine.txt'
        outside.write_bytes(path.read_bytes())
        path.unlink()
        self.symlink(outside, path)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.export()
        self.assertFalse(self.out.exists())

    def test_runtime_directory_symlink_rejected(self):
        link = self.root / 'runtime-alias'
        self.symlink(self.runtime, link)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.export(runtime=link)

    def test_runtime_nested_directory_symlink_rejected(self):
        directory = self.runtime / 'src/particles'
        moved = self.root / 'relocated-particles'
        directory.rename(moved)
        self.symlink(moved, directory)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.export()

    def test_runtime_ancestor_directory_symlink_rejected(self):
        alias = self.root / 'parent-alias'
        self.symlink(self.root, alias)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.export(runtime=alias / 'runtime')

    def test_png_original_is_preserved_byte_for_byte(self):
        import numpy as np
        rgba = np.zeros((4, 4, 4), dtype=np.uint8)
        rgba[1:3, 1:3] = (210, 60, 80, 255)
        source = self.png(rgba)
        convert(source, self.root / 'png-shape')
        self.shape = self.root / 'png-shape/shape.json'
        report = self.export()
        self.assertTrue(report['originalInputPreserved'])
        self.assertEqual((self.out / 'input/original.png').read_bytes(), source.read_bytes())

    def test_standalone_geometry_reports_missing_original(self):
        self.shape = self.root / 'standalone-shape.json'
        self.shape.write_bytes((self.shape_dir / 'shape.json').read_bytes())
        report = self.export()
        self.assertFalse(report['originalInputPreserved'])
        self.assertFalse((self.out / 'input/original.svg').exists())

    def test_destination_symlink_rejected(self):
        target = self.root / 'target'
        target.mkdir()
        alias = self.root / 'output-alias'
        self.symlink(target, alias)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.export(alias / 'child')
        self.assertEqual(list(target.iterdir()), [])

    def test_empty_destination_accepted_nonempty_preserved(self):
        self.out.mkdir()
        self.export()
        marker = self.out / 'keep.txt'
        marker.write_text('keep this exactly', encoding='utf-8')
        before = (self.out / 'export.json').read_bytes()
        with self.assertRaises(ValueError):
            self.export()
        self.assertEqual(marker.read_text(), 'keep this exactly')
        self.assertEqual((self.out / 'export.json').read_bytes(), before)

    def test_runtime_and_repository_destinations_rejected(self):
        for destination in [self.runtime, self.runtime / 'child', ROOT / 'never-create']:
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                self.export(destination)
        self.assertFalse((ROOT / 'never-create').exists())

    def test_motion_and_executable_geometry_keys_rejected(self):
        original = json.loads(self.shape.read_text())
        for key, value in [('engine', {'speed': 999}), ('motion', 'injected'),
                           ('onReady', 'alert(1)'), ('bloomIntensity', 999)]:
            payload = json.loads(json.dumps(original))
            payload['geometry'][key] = value
            self.shape.write_text(json.dumps(payload), encoding='utf-8')
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.export()
            self.assertFalse(self.out.exists())

    def test_top_level_motion_cannot_reach_exported_payload(self):
        payload = json.loads(self.shape.read_text())
        payload['motion'] = {'attackMarker': 90210}
        self.shape.write_text(json.dumps(payload), encoding='utf-8')
        try:
            self.export()
        except ValueError:
            self.assertFalse(self.out.exists())
        else:
            exported = json.loads((self.out / 'input/shape.json').read_text())
            self.assertNotIn('motion', exported)
            self.assertNotIn('attackMarker', (self.out / 'src/main.ts').read_text())

    def test_original_tampering_rejected(self):
        (self.shape_dir / 'original.svg').write_bytes(SVG + b'<!-- tampered -->')
        with self.assertRaises(ValueError):
            self.export()
        self.assertFalse(self.out.exists())

    def test_original_symlink_rejected(self):
        original = self.shape_dir / 'original.svg'
        original.unlink()
        self.symlink(self.source, original)
        with self.assertRaises(ValueError):
            self.export()
        self.assertFalse(self.out.exists())


if __name__ == '__main__':
    unittest.main()
