"""Local viewer with automatic character discovery; credentials are never served."""
import argparse
import json
import math
import re
import struct
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def public_file(base, name, root):
    if not isinstance(name, str) or not name:
        return None
    file = (base / name).resolve()
    if not file.is_relative_to(base.resolve()) or not file.is_relative_to(root.resolve()):
        raise ValueError('Paths must stay inside the character folder')
    relative = file.relative_to(root.resolve())
    if any(p.startswith('.') for p in relative.parts):
        raise ValueError('Hidden paths cannot be published')
    return relative.as_posix() if file.is_file() else None


def glb_ready(file):
    # Avoid listing half-written exports; never load the texture/animation binary here.
    with file.open('rb') as handle:
        header = handle.read(20)
        if len(header) != 20:
            return False
        magic, version, length, chunk, kind = struct.unpack('<5I', header)
        if magic != 0x46546C67 or version != 2 or length != file.stat().st_size or kind != 0x4E4F534A or chunk > length - 20:
            return False
        data = json.loads(handle.read(chunk))
        return bool(data.get('meshes'))


def discover(root=ROOT):
    entries, warnings = {}, []
    legacy = json.loads((root / 'config/characters.json').read_text())
    sources = [(key, value, root) for key, value in legacy.items()]
    for manifest in sorted((root / 'characters').glob('*/character.json')):
        try:
            key = manifest.parent.name
            if key in legacy or not re.fullmatch(r'[a-z][a-z0-9_-]*', key):
                raise ValueError('Reserved or invalid character ID')
            sources.append((key, json.loads(manifest.read_text()), manifest.parent))
        except (ValueError, OSError) as error:
            warnings.append(f'{manifest.parent.name}: {error}')
    for key, spec, base in sources:
        try:
            default = 'assets/animated.glb' if (base / 'assets/animated.glb').exists() else 'assets/static.glb'
            model = public_file(base, spec.get('path', default), root)
            if not model:
                continue
            if not glb_ready(root / model):
                warnings.append(f'{key}: GLB export is not complete')
                continue
            entry = {'title': str(spec.get('title', key)), 'path': model, 'comparisons': {}}
            for field, fallback in [('blend', str(Path(spec.get('path', default)).with_suffix('.blend'))),
                                    ('reference', 'references/turnaround.png'), ('catalog', 'animations/catalog.json')]:
                entry[field] = public_file(base, spec.get(field, fallback), root)
            face = spec.get('face')
            if face is not None:
                if not isinstance(face, list) or len(face) != 3 or not all(isinstance(x, (float, int)) and math.isfinite(x) for x in face):
                    raise ValueError('face must be three finite coordinates')
                entry['face'] = face
            for name, comparison in spec.get('comparisons', {}).items():
                file = public_file(base, comparison['path'], root)
                if file:
                    entry['comparisons'][name] = {'path': file, 'title': str(comparison.get('title', name))}
            entry['revision'] = str((root / model).stat().st_mtime_ns)
            entries[key] = entry
        except (ValueError, OSError, TypeError, KeyError, AttributeError) as error:
            warnings.append(f'{key}: {error}')
    return {'characters': entries, 'warnings': warnings}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def send_head(self):
        # Local editing must not combine a fresh viewer with a cached stylesheet.
        if 'If-Modified-Since' in self.headers:
            del self.headers['If-Modified-Since']
        route = unquote(urlsplit(self.path).path)
        if route == '/api/characters':
            payload = json.dumps(discover(), ensure_ascii=False).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            import io
            return io.BytesIO(payload)
        file = Path(self.translate_path(self.path)).resolve()
        if any(part.startswith('.') for part in Path(route).parts) or not file.is_relative_to(ROOT) or any(part.startswith('.') for part in file.relative_to(ROOT).parts):
            self.send_error(404)
            return None
        if file.is_dir() and not (file / 'index.html').is_file():
            self.send_error(404)
            return None
        return super().send_head()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8770)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Character Lab: http://localhost:{args.port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
