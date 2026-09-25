# Noční elf: třetí samostatná kalibrace

Noční elf má fialovou pleť, stříbrné vlasy, lehkou koženou zbroj a samostatný tmavý plášť. Model nemá luk, toulec ani jinou rekvizitu. Jeho předloha, průřezy, kostra, atlas, klipy a reporty jsou oddělené od strážce i průzkumnice.

## Původ a reprodukce

Vestavěný ImageGen vytvořil **jeden** obrázek 1536 × 1024 se čelem, přesným profilem a zády. Původní [turnaround.png](../references/elf/turnaround.png), [metadata včetně SHA-256](../references/elf/turnaround.json) a [prompt](../config/elf-prompt.txt) zůstávají uložené. Další sestavení běží offline, bez Gemini i bez dalšího generování:

```sh
npm ci
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/elf_pipeline.py build
.venv/bin/python tools/elf_pipeline.py render
npm run serve
```

Otevři `http://localhost:8770/` a vyber **03 / Noční elf**. `elf_pipeline.py` podporuje také `geometry`, `rig`, `motion`, `validate` a `render`; změna geometrie nebo projekce vyžaduje celý `build`. Blender se hledá na PATH, ve standardní macOS aplikaci nebo přes `BLENDER`. Všechny Blender fáze používají `--python-exit-code 1`.

## Co je nově měřené

[elf-profiles.json](../config/elf-profiles.json) ukládá 17 druhů profilů a 106 seřazených řezů. Střed čela je X=281, počátek hloubky profilu X=756, střed zad X=1253, koruna Y=18 a zem Y=944; výška je autorsky 2,5 m. Ucho je samostatný špičatý objem, plášť je samostatný široký díl za trupem a používá vlastní zadní projekci. [elf-rig.json](../config/elf-rig.json) obsahuje klouby fitované na elfa. Anatomická L je +X, R je −X; rig kontroluje centroid každého párového dílu před vážením.

Přední a boční předloha nemají ucho ve stejné výšce. Projekce proto posouvá jeho boční vzorkování o 10 px. Na hlavě zakrývá pixely ucha okolní pletí a vlasy, aby se vedle skutečné geometrie neobjevil druhý boltec. Stříbrná zadní kštice používá pouze pozorované vlasové pixely z pohledu zezadu; chybějící okrajové vzorky se doplňují uvnitř stejného vlasového řádku. Jde o autorskou výplň, ne o rekonstruovaný skrytý povrch.

Uživatel při kontrole upozornil, že hlava elfa i průzkumnice působí proti původnímu strážci úzce. Geometrie elfa proto používá `headWidthScale: 1.45`: maximální šířka hlavního dílu tváře se změnila z **0,189 m na 0,274 m**. UV vzorkování zůstalo na odečtených pixelech předlohy, uši se posunuly jen o rozšíření tváře a krk se rozšířil o polovinu tohoto poměru. U průzkumnice je menší korekce 1,10. [Srovnání stejných kamer před/po](../review/head-width.html) ukazuje obě změny i původního strážce. Poměr je modelářské rozhodnutí podle celého těla, nikoli hodnota automaticky odvozená z fotografie.

## Ověření a výstupy

Finální [elf-animated.glb](../assets/elf-animated.glb) má **61 188 trojúhelníků, 31 242 GLB vertexů, 27 kostí a 214 pojmenovaných klipů**. [Blender soubor](../assets/elf-animated.blend) uchovává 214 actions a aktivní idle; `elf-rigged.blend` uchovává 30 oddělených dílů pro úpravu vah. V `animations/elf/retargeted/` je 214 motion-only GLB pro tuto přesnou hierarchii a `animations/elf/catalog.json` ukládá katalog. Vstupní [report](../review/elf/input-validation.json) a [9 kontrol zdrojových pixelů](../review/elf/projection.json) prošly; finální [validace](../review/elf/validation.json) je **PASS**. Validátor skutečně otevírá každý motion-only soubor a porovnává hierarchii a přesné křivky s finálním GLB. K dispozici je 32 idle klipů a 8 běhů; vyhodnoceno bylo 1284 deformovaných póz.

Statické rendery v `review/elf/` zahrnují celé tělo z čela, ¾, profilu a zezadu a tvář z čela, ¾ a profilu. V browseru byly zkontrolovány `Idle Loop`, KayKit `Running A`, Quaternius `Jog Fwd Loop` a `Sprint Loop`, KayKit `Jump Full Short` a `Waving`, kostra, detail obličeje a přepnutí na obě starší postavy. Konzole nevrátila chyby ani varování. Číselné PASS dokládá topologii, váhy, konečné hodnoty a přenos klipů; nenahrazuje vizuální posouzení všech animací.

Při blízkém profilu jsou místy patrné malované přechody stříbrných vlasů a ucha. Plášť má jednoduché odvozené váhy, ne látkovou simulaci ani kolize, takže při běhu či skoku může protínat nohy. Ruce nemají jednotlivě rigované prsty. V knihovně zůstávají i původní pohyby pojmenované pro luk, ale model žádný luk neobsahuje.
