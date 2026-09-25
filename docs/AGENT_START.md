# Start here: local models, ChatGPT and Gemini

Character Lab does not require one particular coding model. A local model or a cloud model can guide the work. The geometry, rig, animation export and viewer run locally in this repository.

## Choose the model's role

| Role | How to use it | What is implemented here |
|---|---|---|
| Coding / modeling agent | Open this repository in an agent host connected to your chosen local model, OpenAI model or Gemini model. Give it file access, a terminal and a way to inspect images. | Provider-independent scripts and `AGENTS.md`; this repository does not install or configure the agent host. |
| ChatGPT or Gemini chat without repository tools | Supply the relevant instructions, reference images and reports; apply its proposed file changes and run commands yourself. | A reproducible manual workflow. A chat session cannot change local files unless your chosen integration gives it that capability. |
| OpenAI image API | Run `tools/generate_reference.py` with your own local `OPENAI_API_KEY`. | Built-in generation/edit helper, high quality by default, raw image and metadata saved together. |
| Local image model, Gemini or ChatGPT image workflow | Generate a sheet in your own image-capable tool, then import its original output as described below. | Provider-independent reference files. There is no built-in Gemini or local inference API adapter or provider switch. |

A text-only model can help write scripts but cannot visually measure or approve an image. Use a vision-capable model or a human for silhouette measurements, face inspection and motion review. An image generator alone does not perform the measured 3D reconstruction.

## 1. Reproduce the supplied knight first

From the cloned repository root:

```sh
git lfs install
git lfs pull
npm ci
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/pipeline.py build
npm run serve
```

Install Blender first; set `BLENDER` to its executable if automatic discovery fails. On Windows use `.venv\Scripts\python.exe`. Open `http://localhost:8770/` and inspect the actual model and motion. Existing references require no model connection or API key. Do not regenerate them to test setup.

The agent must read `AGENTS.md`, `docs/WORKFLOW.md`, `docs/FACE.md` and `docs/VALIDATION.md` before changing geometry. For ranger or elf also read their separate character document. Stop at a failed stage and fix its cause.

## 2. Create a new character and choose a reference source

```sh
.venv/bin/python tools/new_character.py mage --title "Mage"
```

Edit `characters/mage/config/prompt.txt` to describe the requested character. Include all rules in `config/base-character-rules.txt` regardless of provider: front / true side / back, consistent A-pose and scale, neutral lighting, fitted base clothing, no cloak or protruding equipment. Optional equipment belongs in `characters/mage/accessories/`.

**Built-in OpenAI route:** create your own ignored `.env` from `.env.example`, set `OPENAI_API_KEY`, preview the request, then explicitly generate one reference:

```sh
.venv/bin/python tools/generate_reference.py --character mage --dry-run
.venv/bin/python tools/generate_reference.py --character mage
```

**Local model / Gemini / ChatGPT route:** use the same complete prompt in your chosen image-capable tool. Download the original output file, rather than a screenshot of its UI. Save it in `characters/mage/references/` under a new name. Keep original bytes, including JPEG or WebP if that is what the tool returned; use a separate derived PNG if the modeling script needs one. Do not merely rename another format to `.png`.

Beside the original image, save a JSON metadata file with:

- `provider`, `model` (actual identifier if known, otherwise `null`) and `createdUtc`.
- The complete `prompt` and available generation settings. For local generation record the checkpoint/version, seed and sampler when available.
- `rawFile`, `sha256`, `width`, `height` and input-reference filenames/hashes.
- `usage` and `actualBilledUsd`, both `null` when unknown; do not invent an API cost for a chat download.

For example, compute the fingerprint and dimensions from the actual downloaded file:

```sh
.venv/bin/python - <<'PY'
from pathlib import Path
from PIL import Image
import hashlib
p = Path('characters/mage/references/turnaround.png')  # use the actual filename
with Image.open(p) as image:
    print({'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
           'width': image.width, 'height': image.height})
PY
```

Set `reference` in `characters/mage/character.json` to its relative path, for example `"references/turnaround.png"`. Review the three views before measuring them. If the chosen model cannot produce usable views, obtain a better reference; numeric checks cannot recover unseen anatomy.

## 3. Measure, implement and validate

Follow [the exact file/output contract](CHARACTERS.md). Store measured profiles, projection masks, face landmarks and joints in the new character's `config/`; implement its `tools/model.py`, `tools/build.py` and `tools/rig.py`. Copying another character's pixel coordinates is not calibration.

```sh
.venv/bin/python tools/pipeline.py geometry --character mage
# Inspect static geometry and compare head proportions with the accepted knight.
.venv/bin/python tools/pipeline.py build --character mage
# If the character implements tools/render.py:
.venv/bin/python tools/pipeline.py render --character mage
```

Preserve baselines before corrections. Inspect front, profile, three-quarter, rear, ear roots and neck, then idle, KayKit run, Quaternius jog/sprint, jump, a gesture and skeleton. Report numeric validation separately from observed visual quality. Keep all 214 real source clips and the standard target hierarchy. The running viewer discovers completed character exports automatically.

## If an agent adds another API adapter later

Implement it as an explicit local CLI tool with the same reference/metadata contract. Keep credentials in environment variables or this repository's ignored `.env`, never browser JavaScript. Keep the offline build independent of any generation provider. Preserve original outputs, mandatory prompt rules, duplicate-request protection and honest usage/cost reporting. Read the provider's current official API documentation before selecting endpoints or model identifiers; do not assume OpenAI, Gemini and local servers use identical image APIs. A provider is supported only after the adapter and its request handling have been verified.

## Copy this task into your agent

> Read AGENTS.md and docs/AGENT_START.md, then the linked workflow, face and validation documents. Work only in this clone. First reproduce the knight offline and inspect the viewer. For my new character, create characters/<id>/ and use my chosen reference source: local image model, Gemini, ChatGPT or the built-in OpenAI API helper. Keep raw reference output, complete prompt and honest metadata. Do not invent an unsupported provider connection or regenerate supplied references. Generate the base without a cloak or protruding accessories. Independently measure the new image and implement the documented scripts. Compare head proportions with the knight, preserve baselines, build every dependent stage, and inspect the required views and real motions. Report commands, changed files, actual numeric results, visual observations and remaining limitations. Never print or commit credentials.
