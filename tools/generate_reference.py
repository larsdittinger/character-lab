"""Optional OpenAI reference generation. Offline builds never call this tool."""
import argparse
import base64
import datetime
import hashlib
import io
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'gpt-image-2.5-sunburst'


def api_key():
    key = os.environ.get('OPENAI_API_KEY')
    if not key and (ROOT / '.env').exists():
        for line in (ROOT / '.env').read_text().splitlines():
            match = re.match(r'\s*(?:export\s+)?OPENAI_API_KEY\s*=\s*(.+)', line)
            if match:
                key = match[1].strip().strip('\"\'')
    if not key:
        raise ValueError('Set OPENAI_API_KEY or use this project’s .env')
    return key


def make_request(fields, references):
    if not references:
        return '/images/generations', json.dumps(fields).encode(), 'application/json'
    boundary = 'CharacterLab' + uuid.uuid4().hex
    chunks = []
    for name, value in fields.items():
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    for index, ref in enumerate(references):
        with Image.open(ref) as image:
            content = io.BytesIO()
            image.save(content, format='PNG')
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; filename="reference-{index}.png"\r\nContent-Type: image/png\r\n\r\n'.encode())
        chunks.extend([content.getvalue(), b'\r\n'])
    chunks.append(f'--{boundary}--\r\n'.encode())
    return '/images/edits', b''.join(chunks), f'multipart/form-data; boundary={boundary}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--character', required=True, help='Folder created by tools/new_character.py')
    parser.add_argument('--prompt-file', type=Path)
    parser.add_argument('--name', default='turnaround')
    parser.add_argument('--model', choices=[MODEL, 'gpt-image-2.5-flare'], default=MODEL)
    parser.add_argument('--quality', choices=['low', 'medium', 'high', 'xhigh', 'max'], default='high')
    parser.add_argument('--size', default='1536x1024')
    parser.add_argument('--reference', type=Path, action='append', default=[])
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    for value in [args.character, args.name]:
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', value):
            parser.error('Character and name must be simple filename stems')
    folder = ROOT / 'characters' / args.character
    if not (folder / 'character.json').is_file():
        parser.error('Create the character folder with tools/new_character.py first')
    match = re.fullmatch(r'(\d+)x(\d+)', args.size)
    if not match:
        parser.error('Use explicit WIDTHxHEIGHT, for example 1536x1024')
    w, h = map(int, match.groups())
    if min(w, h) <= 0 or w % 16 or h % 16 or max(w, h) > 3840 or max(w, h) > 3 * min(w, h) or not 655360 <= w * h <= 8294400:
        parser.error('Size must follow GPT Image 2.5 dimension limits; see docs/PRICING.md')
    out = folder / 'references' / (args.name + '.png')
    meta = out.with_suffix('.json')
    lock = out.with_suffix('.pending')
    if any(p.exists() for p in [out, meta, lock]):
        parser.error('Output or request record already exists; choose another --name')
    prompt = (args.prompt_file or folder / 'config' / 'prompt.txt').read_text()
    rules = (ROOT / 'config' / 'base-character-rules.txt').read_text()
    if rules not in prompt:
        prompt += '\n\n' + rules
    fields = dict(model=args.model, prompt=prompt, quality=args.quality,
                  size=args.size, n=1, output_format='png', background='opaque')
    endpoint, body, content_type = make_request(fields, args.reference)
    if args.dry_run:
        print(json.dumps(dict(model=args.model, quality=args.quality, size=args.size,
                              endpoint=endpoint, output=str(out.relative_to(ROOT)),
                              referenceCount=len(args.reference), promptCharacters=len(prompt), networkRequests=0), indent=2))
        return
    key = api_key()
    out.parent.mkdir(parents=True, exist_ok=True)
    metadata = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    provider='OpenAI', model=args.model, quality=args.quality, size=args.size,
                    prompt=prompt, references=[dict(name=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in args.reference],
                    actualBilledUsd=None, endpoint=endpoint)
    # Retain pending records after failures to prevent accidental duplicate paid calls.
    with lock.open('x') as handle:
        json.dump(metadata, handle, indent=2)
    request = urllib.request.Request('https://api.openai.com/v1' + endpoint, data=body,
                                     headers={'Authorization': 'Bearer ' + key, 'Content-Type': content_type})
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            data = json.load(response)
            metadata['requestId'] = response.headers.get('x-request-id')
        images = data.get('data', [])
        if len(images) != 1 or not images[0].get('b64_json'):
            raise ValueError('Expected exactly one PNG response; request record retained')
        raw = base64.b64decode(images[0]['b64_json'], validate=True)
        with Image.open(io.BytesIO(raw)) as image:
            if image.format != 'PNG':
                raise ValueError('The API did not return the requested PNG format')
            metadata['dimensions'] = list(image.size)
            image.verify()
        with out.open('xb') as handle:
            handle.write(raw)
        metadata.update(usage=data.get('usage'), returnedImages=1, sha256=hashlib.sha256(raw).hexdigest(),
                        revisedPrompt=images[0].get('revised_prompt'))
        with meta.open('x') as handle:
            json.dump(metadata, handle, ensure_ascii=False, indent=2)
        lock.unlink()
    except urllib.error.HTTPError as error:
        error.close()
        raise SystemExit(f'OpenAI HTTP {error.code}; no automatic retry. Request record: {lock.relative_to(ROOT)}') from None
    print('Saved', out.relative_to(ROOT), '; usage saved, invoice cost not asserted.')


if __name__ == '__main__':
    main()
