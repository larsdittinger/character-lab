"""Content-addressed stage cache. Verify inputs AND outputs; record successes only."""
import hashlib
import json
import time
from pathlib import Path


def fingerprints(paths):
    result = {}
    for path in sorted(set(map(Path, paths))):
        files = sorted(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('.')) if path.is_dir() else [path]
        if not files:
            result[str(path)] = None
        for file in files:
            if file.is_file():
                with file.open('rb') as handle:
                    digest = hashlib.sha256()
                    for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                        digest.update(chunk)
                    result[str(file)] = digest.hexdigest()
            else:
                result[str(file)] = None
    return result


class BuildCache:
    def __init__(self, directory, force=False):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.force = force
        self.timings = []

    def stage(self, name, inputs, outputs, context, execute):
        start = time.perf_counter()
        stamp = self.directory / (name + '.json')
        signature = {'inputs': fingerprints(inputs), 'context': context}
        try:
            prior = json.loads(stamp.read_text())
        except (OSError, ValueError):
            prior = {}
        actual = fingerprints(outputs)
        hit = not self.force and all(signature['inputs'].values()) and prior.get('signature') == signature and prior.get('outputs') == actual and bool(actual) and all(actual.values())
        if hit:
            print('CACHED', name, flush=True)
        else:
            stamp.unlink(missing_ok=True)
            execute()
            actual = fingerprints(outputs)
            if not actual or not all(actual.values()):
                raise RuntimeError(f'{name}: required output missing')
            temp = stamp.with_suffix('.tmp')
            temp.write_text(json.dumps({'signature': signature, 'outputs': actual}))
            temp.replace(stamp)
        self.timings.append({'stage': name, 'cached': hit, 'seconds': round(time.perf_counter() - start, 4)})
