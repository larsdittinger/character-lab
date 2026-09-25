# Character Lab

Samostatný projekt: obrazová reference → ručně kalibrovaný 3D model → projekční textura → kostra → stažené animace → prohlížeč.

**Strážce má 54 288 trojúhelníků, 27 704 vertexů, 27 kostí a 214 klipů.** Knihovna obsahuje 32 klipů s idle v názvu a 8 běhů. Pohyby pocházejí z Quaternius a KayKit, původní archivy a licence jsou přiložené. Nové masky projekce brání přenosu ucha na nárameník, zbroje na čelist a rukávu na předloketní plát. Ve vieweru lze porovnat aktuální stav s oběma předchozími verzemi.

Druhý charakter, **Lesní průzkumnice**, má **57 584 trojúhelníků, 29 477 vertexů, 27 kostí a 214 klipů**. Používá novou vlastní předlohu a samostatně odečtené proporce včetně samostatných uší. Předloha vznikla jedním voláním vestavěného ImageGen: jeden obrázek obsahuje tři pohledy. Její postup a výstupy popisuje [RANGER.md](docs/RANGER.md).

Třetí charakter, **Noční elf**, má **61 188 trojúhelníků, 31 242 vertexů, 27 kostí a 214 klipů**. Má lehkou zbroj a plášť, bez luku. Jedna nová třípohledová reference, vlastní kalibrace a kontrola proporcí hlavy jsou v [ELF.md](docs/ELF.md). [Srovnání hlav](review/head-width.html) ukazuje korekci elfa i průzkumnice proti původnímu strážci.

## Spuštění hotového výsledku

Potřebuješ Node.js 22+ a Python 3.10+.

```sh
cd character-lab
npm ci
npm run serve
```

Otevři **http://localhost:8770/**. Vlevo nahoře vyber postavu, pod ní pohyb. Dole jsou kamery, kostra a klidová póza. U strážce zvol detail obličeje a v poli „Srovnání projekce“ přepínej „Aktuální model“, „Před opravou projekce“ a „Původní obličej“. Kamera zůstane stejná; kontroluj i celé rameno a boční texturu. [Devět srovnávacích renderů](review/faces.html) lze otevřít samostatně. Port lze změnit: `python3 tools/pipeline.py serve --port 8771`.

## Reprodukce bez dalšího generování

Nainstaluj Blender (ověřeno 5.2.1). Skript ho najde na PATH nebo ve standardní macOS aplikaci; jinak nastav `BLENDER` na cestu k binárce.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm ci
.venv/bin/python tools/pipeline.py build
```

Na Windows použij `.venv\Scripts\python.exe` místo `.venv/bin/python`. Tento příkaz sestaví strážce z přiložených obrázků a animací. Nevolá API a nepotřebuje přístupový klíč. Průzkumnice a elf mají vlastní příkazy v [RANGER.md](docs/RANGER.md) a [ELF.md](docs/ELF.md).

```sh
.venv/bin/python tools/ranger_pipeline.py build
.venv/bin/python tools/elf_pipeline.py build
```

Tím znovu sestavíš druhou a třetí postavu, také offline a bez změny kalibrace strážce.

## Co je přiložené

| Složka / soubor | Obsah |
|---|---|
| [AGENTS.md](AGENTS.md) | Konkrétní zadání a kontroly pro dalšího agenta |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | Technický postup, příkazy, přenos na nový charakter |
| [docs/FACE.md](docs/FACE.md) | Zarovnání obličeje, masky viditelnosti dílů a srovnání |
| [docs/RANGER.md](docs/RANGER.md) | Druhá postava: nová reference, kalibrace a reprodukce |
| [docs/ELF.md](docs/ELF.md) | Třetí postava: noční elf, plášť, vlastní kalibrace a kontrola hlavy |
| [docs/PRICING.md](docs/PRICING.md) | Cena Gemini a volba modelu |
| [docs/VALIDATION.md](docs/VALIDATION.md) | Ověření a známé limity |
| [assets/knight-animated.glb](assets/knight-animated.glb) | Kompletní animovaný model pro Three.js / běžné glTF nástroje |
| [assets/knight-animated.blend](assets/knight-animated.blend) | Model s kostrou a 214 Blender actions |
| [assets/ranger-animated.glb](assets/ranger-animated.glb), [Blender](assets/ranger-animated.blend) | Druhá postava s vlastní kostrou, vahami a 214 přenesenými klipy/actions |
| [assets/elf-animated.glb](assets/elf-animated.glb), [Blender](assets/elf-animated.blend) | Noční elf s lehkou zbrojí, pláštěm a vlastními 214 klipy/actions |
| `assets/knight-rigged.blend` | Kostra a 29 oddělených dílů pro úpravy vah |
| `assets/knight-before-projection.glb`, `assets/knight-before-face.glb` | Zachované srovnávací modely před opravou projekce a před původní opravou tváře |
| `animations/source/` | Původní kompletní bezplatné balíčky, FBX, GLB a licence |
| `animations/retargeted/` | Každý přenesený klip zvlášť, bez duplicitní geometrie |
| `animations/ranger/` | Vlastní katalog a 214 motion-only GLB pro kostru průzkumnice |
| `animations/elf/` | Vlastní katalog a 214 motion-only GLB pro kostru elfa |
| `config/`, `tools/` | Odečtené profily, kostra, masky, prompty a všechny build nástroje |
| `review/` | Validace vstupů, 9 kontrol masek, výstupní validace a renderované kontroly |

Pro dalšího agenta začni [ověřeným pracovním cyklem a tabulkou oprav](docs/WORKFLOW.md#ověřený-pracovní-cyklus-pro-dalšího-agenta) a promptem na konci [AGENTS.md](AGENTS.md). Postup vyžaduje zachování baseline, opravu příčiny, úplný rebuild a srovnání všech důležitých úhlů i pohybů; neúspěšný pokus se vrací. Reprodukce existujícího příkladu je automatická; jiný obrázek potřebuje nové odečtení proporcí. To je rozhodující ruční část workflow.
