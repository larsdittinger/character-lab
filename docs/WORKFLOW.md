# Technický postup

## Ověřený pracovní cyklus pro dalšího agenta

Tento postup zachycuje opravy ověřené na strážci, průzkumnici a nočním elfovi dne **25. 9. 2026**. Souřadnice patří jejich konkrétním předlohám; na další charakter se přenáší postup kontroly, nikoli slepě stejná čísla. Vstupní pravidla jsou v [AGENTS.md](../AGENTS.md), detail tváře v [FACE.md](FACE.md) a další kalibrace v [RANGER.md](RANGER.md) a [ELF.md](ELF.md).

1. **Nejprve reprodukuj známý stav.** Přečti uvedené dokumenty a [VALIDATION.md](VALIDATION.md), použij místní závislosti a existující reference. Spusť `build` vybrané postavy a otevři skutečný animovaný GLB ve vieweru. Pokud některý krok selže, oprav jeho příčinu před dalším krokem. Nevytvářej novou předlohu kvůli chybě projekce nebo vah.
2. **Ulož srovnatelný výchozí stav.** Před experimentem zachovej příslušný GLB, konfiguraci, upravované skripty, atlas a kontrolní rendery v novém adresáři `review/baseline-<datum>-<pokus>/`. Existující historické baseline nepřepisuj. Zaznamenej postavu, konkrétní vadu a pohled, kde je vidět. Srovnávej stejnou kameru, světlo, pózu a u animace také stejný čas klipu.
3. **Najdi příčinu v tomto pořadí:** silueta a objem bez textury → korespondence rysů → správný zdrojový díl → přechod barev. Kontroluj čelo, ¾, profil a zadní projekci. **U nové postavy navíc porovnej šířku a výšku hlavy vůči ramenům a celému tělu se schváleným strážcem při stejné kameře a póze; prohlédni i samotnou tvář, uši a krk.** Číselná validace úzkou hlavu nepozná. Pro přesah ucha na rameno oprav masku viditelnosti; pro dvojité oko nejdřív zarovnání. Širší rozmazání ani jiná kamera nesmí vadu jen schovat.
4. **Měň jednu příčinu v jednom pokusu.** Odděl kalibrace jednotlivých postav. Pro nový díl doplň pojmenování, recept vah a kontrolu stran. Nejprve posuď statický export ze všech kontrolních pohledů. Pokud zlepšení jednoho pohledu poškodí jiný, pokus uprav nebo vrať.
5. **Sestav všechny závislé výstupy.** Geometrie i textura vyžadují pořadí `geometry → rig → motion → validate`, nejjednodušeji celý `build`; pouhá výměna PNG vedle GLB vloženou texturu neaktualizuje. Po úpravě projekce renderuj strážce pomocí `tools/render_faces.py`, průzkumnici pomocí `ranger_pipeline.py render` a elfa pomocí `elf_pipeline.py render`. Zkontroluj aktuální reporty, ne staré PASS z předchozího exportu.
6. **Ověř skutečný pohyb a obraz.** Ve vieweru přepni všechny tři postavy. U upravené postavy přehraj `Idle Loop` (Quaternius 1), `Running A` (KayKit), `Jog Fwd Loop`, `Sprint Loop`, `Jump Full Short` (KayKit) a `Waving` (KayKit). Zapni kostru, zastav a posuň čas v krajních pózách. Zkontroluj ruce, kolena, ramena, pláty a plášť. Pak v klidové póze prohlédni obličej čelně, z ¾ a z profilu, celé tělo včetně zad a čistý tvar. U strážce použij obě uložená srovnání projekce; u elfa a průzkumnice také [srovnání proporcí hlavy](../review/head-width.html). Po načtení nového souboru obnov stránku, ověř zvolenou postavu/klip a konzoli.
7. **Ponech jen prokázané zlepšení a zapiš důkazy.** Podmínkou je současně číselné PASS a viditelné zlepšení bez nalezené regrese v ostatních kontrolních pohledech/pohybech. Pokud pokus nepomohl, vrať jeho kód i konfiguraci a znovu sestav odpovídající výstupy; nenechávej smíchanou starou geometrii a nové animace. Do dokumentace zapiš příčinu, opravu, reprodukční příkaz, skutečné počty, prohlédnuté pohledy/klipy a zbývající omezení. Otevřený viewer je součást předání.

### Rozpoznání již vyřešených chyb

| Viditelný problém | Příčina a správná oprava | Kontrola po opravě |
|---|---|---|
| Druhé oko/obočí na spánku | Neshodné rysy a objem; upravit `config/face.json`, teprve potom míchat barvu | Čelo, ¾ i profil; jeden rys na každé viditelné straně |
| Ucho na nárameníku, zbroj na čelisti, rukáv na plátu | Hloubkový profil zahrnuje zakrývající cizí díl; vymezit platný zdroj v `config/projection.json` | Maskové kontrolní body a skutečný render celého sousedství |
| Bílé pruhy na boku těla či okraji plátu | Do atlasu se vzorkuje pozadí; doplnit okraj pouze platným materiálem stejného dílu ve stejném řádku | Report paddingu; bok a záda včetně chybějícího zdroje |
| Světlá „pleš“ průzkumnice zezadu | Zadní účes má jinou šířku než čelní; nově odečíst `rearHeadRegistration` | Zadní pohled a profil, bez přenosu pleti nebo pozadí do vlasů |
| Druhé ucho nebo hnědý obdélník pod samostatným uchem | Ucho zůstalo namalované i na hlavě; maskovat skutečný obrys ve všech přispívajících zdrojích, s úzkým přechodem | Čelo, ¾ a profil proti uloženému baseline; postup v `RANGER.md` |
| Natažený vodorovný pruh límce | Boční textura vytažená z jediného sloupce; použít dvourozměrné vzorkování uvnitř platného profilu | Šikmý lem límce musí navazovat i z boku |
| Statická póza je dobrá, idle kříží či kroutí končetiny | Prohozené anatomické L/R při odečtu opačné poloviny obrázku; opravit názvy a znovu přiřadit váhy | Centroid L na +X, R na −X; skutečný idle a oba zdroje běhu |
| Hlava v celé postavě působí úzce | Správné pixely reference nezaručují dobrou herní proporci; rozšířit jen geometrii hlavy, podle potřeby posunout uši a šetrně navázat krk | Stejná kamera: strážce proti nové postavě, čelo/¾/profil i celá postava; po přijetí znovu rig a klipy |
| Validátor označí podzemní spawn za rozpad modelu | Celá dráha rootu zaměněná za velikost těla; měřit rozsah jednotlivé deformované pózy zvlášť | Zachovat zdrojový pohyb, reportovat dráhu a požadavky na scénu |

## Co rozhoduje AI a co generují skripty

Workflow kombinuje modelářská rozhodnutí AI agenta s programovým sestavením geometrie. Agent nemodeluje myší vertex po vertexu. Prohlédne předlohy, odečte proporce, určí průřezy, polohy kloubů a korespondence rysů, zapíše je do konfigurace a upraví potřebný kód. Potom výsledek vizuálně kontroluje a opravuje. Označení „ruční kalibrace“ zde znamená toto individuální odečtení a rozhodování, nikoli automatickou detekci obrázku skriptem.

| Část | Kdo ji provádí |
|---|---|
| Vytvoření referenčních obrázků | Obrazový model; původní strážce používá Gemini, původ nové reference je zaznamenán u dané postavy |
| Odečtení proporcí, návrh tvaru a oprav | AI agent podle obrázků a kontrolních pohledů |
| Sestavení ploch, UV atlasu, kostry a vah | Přiložené Python/Blender skripty podle uložených hodnot |
| Původní pohybové křivky | Stažené animace Quaternius a KayKit |
| Přizpůsobení animací proporcím postavy | Retarget skript a IK |
| Posouzení vzhledu a další iterace | AI agent; výsledný vzhled může posoudit uživatel ve vieweru |

**Existujícího strážce lze znovu sestavit automaticky bez AI a bez dalšího generování obrázku.** U nové postavy samotná výměna PNG nestačí: agent musí znovu odečíst proporce, upravit konfiguraci a ověřit výsledek. Slabší model proto může snadno zopakovat dodaný příklad; jeho schopnost vytvořit stejně kvalitní novou postavu tím ještě není prokázaná.

## 1. Reference

Gemini vytvoří rastrovou předlohu. Nevytváří v tomto projektu mesh ani animaci. Aktuální strážce používá původní společný předek/profil a druhý doplňkový zadní obrázek. Původní první výstup měl navíc duplicitní profil; raw soubor zůstal zachován. `prepare.py` připraví kalibrované výřezy. Historický log je `references/generation.json`.

Pro příští charakter doporučujeme **předek + skutečný 90° bok + záda v jednom obrázku**, stejná A-póza, stejná výška, rovnoměrné světlo, žádné perspektivní zkrácení. Všechny potřebné strany jsou pak k dispozici před modelováním. Společný obrázek pomáhá konzistenci, ale nezaručuje přesnou shodu rysů. Pro blízké záběry tváře má smysl zvláštní velký head turnaround; je to další placený obrázek.

Volitelný generátor je samostatný, nemá přístup k žádným sousedním projektům:

```sh
# Bez síťového požadavku:
.venv/bin/python tools/generate_reference.py --dry-run
# Nový placený výstup, klíč v GEMINI_API_KEY nebo místní .env:
.venv/bin/python tools/generate_reference.py --name new-turnaround --size 2K
# Zachování identity při nové referenci:
.venv/bin/python tools/generate_reference.py --name new-views --reference references/gemini-original.png
```

Před novou postavou uprav text `config/turnaround-prompt.txt`. Výstupy se nepřepisují; pro každý pokus zvol nový název. Vedle PNG se ukládá prompt, model, čas a usageMetadata. Pomocník nedělá automatické opakované placené pokusy. Druhá postava má vlastní reference a postup v [RANGER.md](RANGER.md); její původ se neposuzuje podle historického logu Gemini pro strážce.

Nová reference průzkumnice vznikla **jedním voláním vestavěného ImageGen**, bez nového volání Gemini. Výstup je jeden obrázek 1536 × 1024 se třemi pohledy. Originál a metadata jsou v `references/ranger/turnaround.png` a `.json`, prompt v `config/ranger-prompt.txt`. Metadata neuvádějí změřenou účtovanou cenu.

Stejně tak reference nočního elfa vznikla jedním voláním vestavěného ImageGen: jeden obrázek 1536 × 1024 se třemi pohledy. Originál, metadata a prompt jsou v `references/elf/` a `config/elf-prompt.txt`; detaily v [ELF.md](ELF.md). Offline rebuild reference znovu negeneruje.

## 2. Kalibrace a měření

Aktuální pracovní obrázek má 1907 × 1280 px. Střed čela je X=494, hloubkový počátek profilu X=1230, vršek Y=72, zem Y=1215. Výška charakteru je autorsky zvolených 2.5 m. Měřítko je `2.5 / (1215 - 72)`. Ve výsledném GLB je Y nahoru a +Z dopředu.

`config/profiles.json` obsahuje 17 druhů průřezů a 120 odečtených řezů. Každý řádek má `[y, levýObrysZepředu, pravýObrysZepředu, předníObrysZBoku, zadníObrysZBoku]`. Párové díly se zrcadlí. Znak a přezka mají vlastní zvýšené plochy v `model.py`. Dohromady vznikne 29 uzavřených dílů.

Po přípravě výřezů pipeline spustí `tools/validate_inputs.py`: ověří rozměr kalibrace, konečné souřadnice, kladnou šířku a hloubku řezů, rostoucí Y, korespondence tváře a nenulové délky kostí. Report `review/input-validation.json` ukládá také SHA-256 původních předloh a konfigurací. `model.py` navíc porovnává otisky obou raw obrázků s očekávanými hodnotami v `config/projection.json`; změna reference se starými maskami skončí chybou.

Pro jiný obrázek:

1. Zachovej originál. Urči výřezy, měřítko a společné výškové body všech pohledů.
2. Uprav `prepare.py`, jeho cropy a referenční souřadnice v `model.py`.
3. Odečti profily jednotlivých částí. V Y musí být seřazené a bez duplicit.
4. Uprav zadní projekci: její střed, měřítko a výškové korespondence v `model.py`.
5. Pro tvář zvlášť uprav `config/face.json` a reliéf nosu/rtů.
6. V `config/projection.json` znovu označ skutečně viditelné části každého zdroje. Odděl ucho od ramene, čelist od zbroje a plát od rukávu. Ulož nové kontrolní body a identitu zdroje až po této kalibraci.
7. Teprve po kontrole statického modelu přesuň klouby v `config/rig.json` a dolaď váhy. Druhou dodanou postavu upravuj v jejím vlastním postupu podle [RANGER.md](RANGER.md), aby kalibrace strážce zůstala zachovaná.

Jde o řízenou rekonstrukci, nikoli o automatickou fotogrammetrii. Z neviděných míst nelze odvodit přesný původní povrch; jejich objem je modelářské rozhodnutí.

## 3. Geometrie a textura

`model.py` interpoluje odečtené průřezy hladkou kubickou interpolací zachovávající tvar. Kolem každého průřezu rozmístí 64 segmentů, uzavře konce a doplní reliéf obličeje. Tvar průřezu lze měnit exponentem: příliš plochá tvář tahá boční rysy dopředu. Obvodový šev je geometricky svařený.

Pro každý díl se barva promítá z předku a podle potřeby profilu a zad. **Hloubkový obrys dílu neříká, zda je v obrázku vidět:** stejné souřadnice mohou v profilu patřit uchu, které nárameník zakrývá. `config/projection.json` proto odděleně popisuje viditelnost pomocí řádků `[imageY, levéX, pravéX]` a případných vyloučených polygonů.

- `front-fallback` sníží boční příspěvek na nulu tam, kde zdroj patří jiné části postavy; použije čelní projekci téhož dílu. Platí pro nárameníky a předloketní pláty.
- `clamp-valid-source` přesune souřadnice zakryté oblasti do nejbližšího platného materiálu. Chrání čelist, vlasy, zátylek a členitou čelní hranu ramene. Je to řízené doplnění textury, nikoli rekonstrukce neviditelné anatomie.

Masky drží 2 px odstup od hrany a 3 px přechod na platné straně. Devět kontrol známých kolizí zdrojových souřadnic a počty upravených vzorků jsou v `review/projection.json`. Pro obličej se navíc před mícháním zarovnají výšky rysů a hloubkové korespondence. Jemné rysy dostávají užší přechod, nízkofrekvenční barva širší. Konkrétní měření a devět porovnávacích renderů popisuje [FACE.md](FACE.md).

Čelní projekce má navíc ochranu proti bílému studiovému pozadí v `frontBackgroundGuard`. Vybere světlou neutrální oblast spojenou s okrajem obrázku a rozšíří ji o 2 px, aby odstranila i světlý okraj siluety. Zasažené souřadnice přesune na nejbližší platný pixel **ve stejném řádku a měřeném intervalu stejného dílu**. Zachová tím kresbu materiálu na trupu, pažích a bocích bez rozmazání celé textury. Když v daném řádku není žádný platný zdroj, použije zvolenou základní barvu materiálu a zaznamená to zvlášť. Počty přesunutých vzorků, chybějícího zdroje a zbývajícího pozadí jsou v `frontBackgroundPadding` v reportu projekce.

Výsledné barvy se vypálí do jednoho UV atlasu 2640 × 4704 px s okrajovou výplní ostrovů. Blender načte mesh, svaří shodné body, přepočítá normály, redukuje hustotu a exportuje GLB s vloženou texturou. Oddělené díly zůstanou v `.blend`, GLB má jednu mesh primitive a materiál. Textura obsahuje namalované světlo; proto viewer používá mírné fyzikální stínování, nikoli agresivní lesk.

## 4. Kostra a váhy

`rig_character.py` převede model do Blender Z-up, vytvoří 23 humanoidních kostí podle `config/rig.json` a přidá 4 kosti tabardu. Osy vycházejí z dodaného zdrojového rig popisu `config/source-rig.json`. Pro přegenerování tohoto popisu slouží `inspect_source_rig.py`.

Váhy se přiřadí podle dílu a polohy. Hlava patří hlavě, nárameník klíční kosti, předloketní plát předloktí, rukavice ruce. Měkké spoje mají hladký přechod, tabard směs pánve a dvou bočních kostí. Každý vertex má normalizované váhy. Není použito slepé automatické vážení přes celou zbroj.

Názvy L/R jsou **anatomické strany**, ne strany obrázku: v pracovním systému Y-up, +Z dopředu leží L na +X a R na −X. Oba rig skripty před vážením kontrolují znaménko centroidu párového dílu. Strážce a průzkumnice mají základní profil odečtený z opačných polovin čelní reference; bez této kontroly by se váhy přiřadily protějším končetinám. Normalizace vah ani test konečných souřadnic takovou záměnu samy neodhalí. Po přejmenování dílů znovu vytvoř rig i animace a prohlédni idle a běh.

## 5. Skutečné stažené animace

Zdroje jsou oficiální volné balíčky:

- [Quaternius Universal Animation Library](https://quaternius.itch.io/universal-animation-library), Standard.
- [Quaternius Universal Animation Library 2](https://quaternius.itch.io/universal-animation-library-2), Standard.
- [KayKit Character Animations](https://kaylousberg.itch.io/kaykit-character-animations), bezplatný balík 1.1.

Původní zipy, všechny rozbalené soubory a licence jsou v `animations/source/`. `sources.json` obsahuje odkazy, autory, velikosti a SHA-256 archivů. Jde o celé dostupné bezplatné archivy, nikoli o zakoupené Pro/Source verze. Autoři Quaternius a Gonzalo Furnier, Kay Lousberg / KayKit; příslušné license soubory zůstaly zachované. Animace mají CC0; tím automaticky neoznačujeme celý Gemini obrázek za CC0.

Opětovné získání: `python3 tools/download_animations.py`. Existující zipy se znovu nestahují. Nástroj prochází oficiální free-download flow itch.io; pokud se web změní, skončí chybou a agent musí ověřit nový oficiální postup. Nikdy nehádá placený upload.

Pro cílový rig vybíráme UAL1/UAL2 bez `_RM` a KayKit Rig_Medium. Ostatní rigy i root-motion verze zůstávají v raw knihovně. T-pózy a experimentální rozpad/transformace nejsou přidávány jako duplicitní běžné klipy. Výsledkem je 214 pojmenovaných klipů včetně několika statických póz. Přesný seznam je `animations/catalog.json`.

## 6. Přenos pohybu

`retarget.mjs` provede pro každý klip:

1. Načte glTF transformace, hierarchii a zdrojové křivky. Vyhodnotí je ve 30 Hz včetně koncového vzorku.
2. Zjistí změnu světové rotace každé zdrojové kosti proti klidové póze. Mapuje názvy KayKit na cílovou humanoidní hierarchii.
3. Srovná cílovou A-pózu rukou se zdrojovou T-pózou podle vektorů mezi klouby. Tím se vyhne chybám kanonizovaných os GLB exportéru.
4. Přenese rotace a root/pelvis posuny se škálováním podle délky nohy. Lokální rotaci cíle dopočítá z požadované světové a rotace rodiče.
5. Analytické dvoukloubové IK přizpůsobí nohy cílovým délkám. Dráha kotníku se počítá vzhledem ke zdrojové kyčli a přenese k cílové kyčli. Zachová se zdrojový směr kolena. Není to simulace kontaktu s terénem.
6. Kosti tabardu odvodí omezenou část pohybu stehen. Nejde o simulovanou látku.
7. Uloží běžné glTF křivky. Quaterniony normalizuje a sjednotí znaménka mezi vzorky, aby interpolace neotáčela kost o dlouhou cestu.

Animované škálování zdrojových kostí ignorujeme: některé spawn efekty škálují na nulu, což není přenosný lidský kloubový pohyb. Takové klipy přenášejí pózu, nikoli kompletní efekt vznikání/rozpadání. Ruce mají celistvé rukavice bez jednotlivých prstů; zdrojové prstové křivky se nepřenášejí. Pose klipy dostanou minimální délku 1/30 s, aby časy byly platné a rostoucí.

`export_clips.mjs` uloží každý klip samostatně se stejnou kostrou, ale bez opakování 10MB textury. `save_animated.py` importuje finální GLB do Blenderu a uchová všech 214 actions s fake user. V Action Editoru vyber požadovanou akci; NLA tracky jsou při otevření ztlumené a aktivní je idle.

Všechny tři postavy používají společné skripty pro přenos, export klipů a validaci. `tools/character_paths.mjs` vybere cesty podle `CHARACTER_LAB_CHARACTER` (`knight` je výchozí; další hodnoty jsou `ranger` a `elf`). Jejich motion wrapper nastaví tuto hodnotu a importuje společný skript; neupravuje jeho zdrojový text. Stejná oprava retargetingu tak platí pro všechny tři cílové rigy.

## 7. Viewer a kontrola

Three.js GLTFLoader načte vložený materiál, skin i AnimationClips. Vlevo nahoře lze přepínat strážce, průzkumnici a elfa. Kamera vychází z rozměrů načteného modelu a z cíle obličeje dané postavy; statistiky se počítají ze skutečného GLB. AnimationMixer přehrává vybraný klip, přechody mezi klipy trvají 0.18 s. Při načtení statického modelu se animační ovládání vypne.

Kamera, scrubber, rychlost, kostra a čistý tvar usnadňují hodnocení. Strážce má pole „Srovnání projekce“: aktuální model, `knight-before-projection.glb` a historický `knight-before-face.glb`. Přepnutí zachová kameru a porovnává klidovou pózu. Kliknutí na animaci vrátí aktuální model. Reference i odkazy ke stažení odpovídají vybrané postavě. Žádná externí CDN není nutná; importy vedou do místního `node_modules`.

`npm run validate` kontroluje GLB hodnoty, časy, quaterniony, váhy a topologii strážce, pak vyhodnotí všech 214 klipů a 1284 vzorkovaných póz včetně skutečného skinningu. Rozsah modelu posuzuje v každé póze zvlášť, odděleně od posunu celé postavy během klipu. Otevře také všech 214 motion-only GLB: musí být bez meshů a textur, se stejnou cílovou hierarchií, kanály, interpolací i přesnými časovými a hodnotovými křivkami jako odpovídající klipy finálního animovaného strážce. Počet actions z reportu Blender exportu musí odpovídat katalogu. Nenahrazuje to vizuální kontrolu kontaktů, kolizí ani proporcí hlavy; další dvě postavy mají vlastní reporty. Viz [VALIDATION.md](VALIDATION.md), [RANGER.md](RANGER.md) a [ELF.md](ELF.md).

## Mapování příkazu na výstup

| Příkaz | Výstup |
|---|---|
| `pipeline.py geometry` | Kalibrace, kontrola vstupů a identity zdrojů, masky, `model.json`, atlas, static GLB/Blend |
| `pipeline.py rig` | `knight-rigged.glb`, oddělené díly + armature v Blend |
| `pipeline.py motion` | 214 klipů ve GLB, jednotlivé klipy a animated Blend |
| `pipeline.py validate` | `review/validation.json` |
| `pipeline.py build` | Všechny čtyři předchozí kroky v pořadí |
| Blender `--python tools/render_faces.py` | 9 renderů: historický stav, baseline projekce a aktuální model, vždy čelo/¾/profil |

## Druhý samostatně kalibrovaný charakter

```sh
.venv/bin/python tools/ranger_pipeline.py build
.venv/bin/python tools/ranger_pipeline.py render
```

Ranger pipeline podporuje také samostatné fáze `geometry`, `rig`, `motion` a `validate`; respektuje stejnou proměnnou `BLENDER`. Používá `config/ranger-profiles.json`, `config/ranger-rig.json` a vlastní předlohu. Výstupy mají prefix `ranger-`, katalog a 214 jednotlivých klipů jsou v `animations/ranger/`, reporty a sedm kontrolních renderů v `review/ranger/`. Pohyby vycházejí ze stejných stažených archivů přes společný retarget kód s oddělenými cestami k výstupům. Všechny pipeline spouštějí Blender s `--python-exit-code 1`: výjimka v jeho Python skriptu zastaví build. Podrobná kalibrace, samostatné uši a oprava projekce vlasů jsou v [RANGER.md](RANGER.md).

## Třetí samostatně kalibrovaný charakter

```sh
.venv/bin/python tools/elf_pipeline.py build
.venv/bin/python tools/elf_pipeline.py render
```

Elf používá `config/elf-profiles.json`, `config/elf-rig.json` a jednu vlastní uloženou třípohledovou předlohu. Výstupy mají prefix `elf-`, klipy a katalog leží v `animations/elf/` a reporty s rendery v `review/elf/`. Vstupní validace kontroluje 17 typů profilů, 106 řezů, otisk zdroje a 9 známých bodů zdrojového vlastnictví. Podrobný postup, před/po proporcí a limity jsou v [ELF.md](ELF.md).

Build je deterministický vzhledem k uloženým obrázkům a konfiguraci, ale exportní pořadí a redukce se mohou mírně lišit mezi verzemi Blenderu. Nové generování reference není deterministické. Ověřené prostředí: Blender 5.2.1, Three.js 0.180.0, Python 3.14, NumPy 2.5.3, Pillow 12.3.0.
