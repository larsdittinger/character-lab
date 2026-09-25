"""Offline regression checks for discovery, cache invalidation and API requests."""
import json
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import base64
import io
import urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_cache import BuildCache
from generate_reference import make_request
import generate_reference
from new_character import create_character
from serve import discover
from PIL import Image


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'config').mkdir()
        (self.root / 'config/characters.json').write_text('{}')
        (self.root / 'config/turnaround-prompt.txt').write_text('A measured character')

    def tearDown(self):
        self.temp.cleanup()

    def model(self, folder):
        # Valid GLB container for discovery only; not a replacement pipeline output.
        data = json.dumps({'asset': {'version': '2.0'}, 'meshes': [{'primitives': []}]}).encode()
        data += b' ' * ((4 - len(data) % 4) % 4)
        (folder / 'assets/static.glb').write_bytes(struct.pack('<5I', 0x46546c67, 2, len(data) + 20, len(data), 0x4e4f534a) + data)

    def test_scaffold_discovery_and_incomplete_export(self):
        folder = create_character('mage', 'Mage', self.root)
        self.assertFalse(discover(self.root)['characters'])
        self.model(folder)
        record = discover(self.root)['characters']['mage']
        self.assertEqual(record['path'], 'characters/mage/assets/static.glb')
        self.assertIsNone(record['catalog'])
        with self.assertRaises(FileExistsError):
            create_character('mage', 'Overwrite', self.root)
        file = folder / 'assets/static.glb'
        file.write_bytes(file.read_bytes()[:-1])
        self.assertFalse(discover(self.root)['characters'])

    def test_bad_manifest_isolated_and_path_escape_rejected(self):
        good = create_character('good', 'Good', self.root)
        self.model(good)
        bad = create_character('bad', 'Bad', self.root)
        (bad / 'character.json').write_text('{invalid')
        self.assertEqual(list(discover(self.root)['characters']), ['good'])
        (bad / 'character.json').write_text(json.dumps({'path': '../../characters/good/assets/static.glb'}))
        self.assertEqual(list(discover(self.root)['characters']), ['good'])
        self.assertIn('Paths must stay', discover(self.root)['warnings'][0])
        for name in ['../bad', 'knight', 'Bad Name']:
            with self.assertRaises(ValueError):
                create_character(name, 'Bad', self.root)

    def test_cache_checks_content_missing_outputs_and_failure(self):
        source, output = self.root / 'input', self.root / 'output'
        source.write_text('first')
        count = []
        def build():
            count.append(1)
            output.write_text(source.read_text())
        cache = BuildCache(self.root / 'cache')
        def stage():
            cache.stage('test', [source], [output], {'version': 1}, build)
        stage(); stage()
        self.assertEqual(len(count), 1)
        source.write_text('other'); stage()
        self.assertEqual(output.read_text(), 'other')
        output.write_text('corrupt'); stage()
        output.unlink(); stage()
        self.assertEqual(len(count), 4)
        def fail():
            output.write_text('partial')
            raise RuntimeError('failed stage')
        with self.assertRaises(RuntimeError):
            BuildCache(self.root / 'cache', force=True).stage('test', [source], [output], {}, fail)
        self.assertFalse((self.root / 'cache/test.json').exists())
        stage()
        self.assertEqual(output.read_text(), 'other')

    def test_generation_payload_and_reference_edit(self):
        fields = {'model': 'gpt-image-2.5-sunburst', 'quality': 'high', 'n': 1, 'size': '1536x1024', 'prompt': 'test'}
        endpoint, body, content_type = make_request(fields, [])
        self.assertEqual(endpoint, '/images/generations')
        self.assertEqual(json.loads(body), fields)
        image = self.root / 'input.png'
        Image.new('RGB', (16, 16)).save(image)
        endpoint, body, content_type = make_request(fields, [image])
        self.assertEqual(endpoint, '/images/edits')
        self.assertIn(b'name="image[]"', body)
        self.assertIn(b'\x89PNG', body)
        self.assertIn('multipart/form-data', content_type)

    def test_generation_preserves_raw_bytes_rules_usage_and_refuses_overwrite(self):
        folder = create_character('mage', 'Mage', self.root)
        (self.root / 'config/base-character-rules.txt').write_text('No cape or protruding accessories.')
        raw = io.BytesIO()
        Image.new('RGB', (16, 16)).save(raw, format='PNG')
        result = {'data': [{'b64_json': base64.b64encode(raw.getvalue()).decode()}], 'usage': {'output_tokens': 17}}
        response = io.BytesIO(json.dumps(result).encode())
        response.headers = {'x-request-id': 'test-only'}
        argv = ['generate_reference.py', '--character', 'mage']
        with patch.object(generate_reference, 'ROOT', self.root), patch.object(sys, 'argv', argv), patch.object(generate_reference, 'api_key', return_value='test-only'), patch.object(generate_reference.urllib.request, 'urlopen', return_value=response) as call:
            generate_reference.main()
            payload = json.loads(call.call_args.args[0].data)
            self.assertIn('No cape', payload['prompt'])
            self.assertEqual(payload['quality'], 'high')
            self.assertEqual(call.call_count, 1)
            with self.assertRaises(SystemExit):
                generate_reference.main()
            self.assertEqual(call.call_count, 1)
        self.assertEqual((folder / 'references/turnaround.png').read_bytes(), raw.getvalue())
        metadata = json.loads((folder / 'references/turnaround.json').read_text())
        self.assertEqual(metadata['usage'], result['usage'])
        self.assertIsNone(metadata['actualBilledUsd'])
        self.assertFalse((folder / 'references/turnaround.pending').exists())

    def test_failed_paid_request_is_not_automatically_retried(self):
        folder = create_character('mage', 'Mage', self.root)
        (self.root / 'config/base-character-rules.txt').write_text('No cape')
        error = urllib.error.HTTPError('https://api.openai.com/v1/images/generations', 429, 'Rate limit', {}, None)
        with patch.object(generate_reference, 'ROOT', self.root), patch.object(sys, 'argv', ['generate_reference.py', '--character', 'mage']), patch.object(generate_reference, 'api_key', return_value='test-only'), patch.object(generate_reference.urllib.request, 'urlopen', side_effect=error) as call:
            with self.assertRaises(SystemExit):
                generate_reference.main()
            self.assertEqual(call.call_count, 1)
            self.assertTrue((folder / 'references/turnaround.pending').exists())
            with self.assertRaises(SystemExit):
                generate_reference.main()
            self.assertEqual(call.call_count, 1)


if __name__ == '__main__':
    unittest.main()
