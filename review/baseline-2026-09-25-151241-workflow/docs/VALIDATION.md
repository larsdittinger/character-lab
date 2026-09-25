# Kontroly a známé limity

Výstupní validace strážce je v `review/validation.json`; reporty vstupů, projekce, geometrie, vah a Blender actions jsou vedle něj. `npm run validate` ověří hotové výstupy. `.venv/bin/python tools/pipeline.py build` nejprve ověří vstupy, vše znovu sestaví a teprve potom validuje výstupy. Průzkumnice a elf mají samostatné reporty a postupy v [RANGER.md](RANGER.md) a [ELF.md](ELF.md).

## Číselně ověřeno na strážci

- `review/input-validation.json`: **PASS**, 17 druhů profilů, 120 měřených řezů, kalibrace 1907 × 1280. Souřadnice jsou konečné, řezy mají rostoucí Y a kladnou šířku/hloubku, odpovídají rozměrům předlohy; kontrolují se i korespondence tváře a délky kostí.
- Report ukládá SHA-256 raw předloh a konfigurací. `model.py` ověřuje identitu původního i zadního obrázku vůči `config/projection.json`; staré masky nelze potichu použít po výměně těchto souborů.
- `review/projection.json`: **PASS**, všech **9** kontrol povolených/zakázaných souřadnic prošlo. Zakázaný boční příspěvek pro nárameníky a předloktí je nulový; čelist a vlasy čerpají z omezené platné oblasti. Oprava projekce nemění geometrii.
- Ochrana čelní projekce před propojeným studiovým pozadím kontroluje 27 loftovaných dílů. Report uvádí 641 518 opravených vzorků, 27 648 vzorků bez dostupného materiálu v daném řádku nahrazených základní barvou a **0 zbývajících vzorků pozadí** mimo tuto náhradu. Jde o vzorky atlasových dílů, nikoli o počet unikátních pixelů původního obrázku. Chybějící zdroj zůstává přiznanou aproximací.

- 54 288 trojúhelníků, 27 704 GLB vertexů, 27 kostí.
- 29 původních dílů; každý má 0 otevřených a 0 non-manifold hran.
- `review/validation.json`: **PASS**, 214 unikátně pojmenovaných klipů a 214 actions zaznamenaných v reportu Blender exportu. Počty katalogu, finálního GLB a actions se shodují. Patří sem i krátké statické pose klipy; nejde o 214 lokomočních cyklů.
- Skutečně otevřeno všech **214 souborů** v `animations/retargeted/`. Každý obsahuje jeden správně pojmenovaný klip, žádný mesh ani texturu a přesně stejnou cílovou hierarchii, animační kanály, interpolaci, časy a hodnoty křivek jako příslušný klip v `knight-animated.glb`. Jde o shodu s přenesenými klipy cílového modelu, nikoli o tvrzení, že retargeting nemění originální zdrojová data.
- 32 klipů obsahuje Idle v původním názvu a má délku nad 0.1 s, 8 různých běhů. Minimum 5+5 je splněné bez přejmenovaných kopií.
- Všechny accessors mají konečné číselné hodnoty; časy klipů jsou striktně rostoucí a quaterniony normalizované.
- Maximální odchylka součtu vah je přibližně 0.00000009. Nejvyšší numerická odchylka IK kotníku od zadaného cíle je pod 0.00001 m. To neznamená stejnou přesnost kontaktu s podlahou.
- 1284 vzorkovaných póz (6 na každý klip) se skutečně vyhodnotí v Three.js včetně skinningu. Kontrola nenašla NaN ani rozpad do extrémního objemu; největší rozměr jedné vzorkované pózy strážce je 3.127 m.

## Číselně ověřeno na průzkumnici

`review/ranger/validation.json`: **PASS**, 57 584 trojúhelníků, 29 477 vertexů finálního GLB, 27 kostí, 214 klipů, 214 motion-only souborů a 214 Blender actions. Knihovna opět obsahuje 32 idle a 8 běhů; vyhodnoceno bylo 1284 póz. Samostatné soubory v `animations/ranger/retargeted/` se porovnávají s cílovým GLB průzkumnice.

Maximální odchylka součtu vah je přibližně 0.00000003 a odchylka IK kotníku od zadaného cíle pod 0.00001 m. Největší rozměr vzorkovaného modelu v jedné póze je 2.937 m. Společný validátor posuzuje rozsah každé pózy zvlášť; celkovou dráhu rootu zachovává v reportu a nezaměňuje větší posun celého charakteru za rozpad geometrie. Přenos zdrojového pohybu sám neřeší kontakt s podlahou. Reprodukce: `.venv/bin/python tools/ranger_pipeline.py build`; samotná kontrola: `.venv/bin/python tools/ranger_pipeline.py validate`.

Po uživatelské připomínce se geometrie hlavy průzkumnice rozšířila o 10 %, z 0,311 m na 0,342 m. Statické pohledy před/po a schválený strážce jsou na [stránce proporcí](../review/head-width.html). Následný rig, všechny přenesené klipy a validace byly znovu sestavené; výše uvedené finální počty zůstaly stejné.

## Číselně ověřeno na nočním elfovi

`review/elf/input-validation.json`: **PASS**, 17 typů profilů a 106 měřených řezů, kalibrace 1536 × 1024 a shoda SHA-256 uložené předlohy. `review/elf/projection.json`: **PASS**, 9 konkrétních povolených/zakázaných zdrojových bodů pro ucho, tvář, vlasy, zbroj, plášť a pozadí. Tyto body nekontrolují kvalitu všech přechodů na atlasu.

`review/elf/validation.json`: **PASS**, 61 188 trojúhelníků, 31 242 vertexů ve finálním GLB, 27 kostí, 214 klipů, 214 skutečně otevřených a přesně porovnaných motion-only souborů a 214 Blender actions. Zůstalo 32 idle a 8 běhů; vyhodnoceno bylo 1284 deformovaných póz. Maximální odchylka součtu vah je přibližně `6.71e-8`, odchylka IK kotníku pod `0.00001 m` a největší rozměr jedné pózy přibližně `3.130 m`. Po opravě proporce je šířka hlavního dílu tváře 0,274 m proti 0,189 m před ní. Reprodukce: `.venv/bin/python tools/elf_pipeline.py build`; rendery: `.venv/bin/python tools/elf_pipeline.py render`. Původ, konkrétní opravy a limity popisuje [ELF.md](ELF.md).

## Vizuální srovnání

`tools/render_faces.py` vytvoří devět pohledů ze skutečných GLB se stejným nastavením kamery a světel: `face-before-*` pro historický obličej, `face-baseline-*` pro stav před opravou přesahů a `face-after-*` pro aktuální výsledek. Každá trojice zahrnuje čelo, ¾ a profil. [Srovnávací stránka](../review/faces.html) a [FACE.md](FACE.md) umožňují posoudit vzhled odděleně od číselných reportů.

Kontrola masek dokazuje dodržení uložených oblastí. Sama nepotvrzuje správnost všech jejich hranic ani kvalitu doplněné zakryté textury. Stejně tak report 1284 póz potvrzuje konečné hodnoty a přijatelný rozsah skinningu, nikoli ruční posouzení každé pózy.

### Záznam vizuální kontroly — 25. 9. 2026

Ve skutečném Chrome vieweru byly na obou postavách prohlédnuty `Idle Loop` (Quaternius 1), `Running A` (KayKit), `Jog Fwd Loop`, `Sprint Loop`, `Jump Full Short` (KayKit), `Waving` (KayKit) a zobrazená kostra. U průzkumnice proběhla tato kontrola až po opravě anatomických stran a vah: ruce v idle a běhu se již nepřiřazují protějším kostem. Skok se kontroloval také zastavením a posunem času. Výchozí kamera během vyšší fáze skoku může oříznout vršek hlavy; pro posouzení celé trajektorie je potřeba oddálit pohled.

Po načtení finálních textur byly v browseru znovu prohlédnuty čelo, ¾ a profil obou postav. U strážce se stejnou kamerou fungují oba uložené srovnávací modely: historické zdvojení očí a pozdější přesah ucha/zbroje jsou odlišné výchozí vady. Aktuální projekce tyto výrazné přesahy odstraňuje. Průzkumnice má samostatně doložené [srovnání ucha a límce](../review/ranger/detail-comparison.html); její poslední úprava mění projekci, shoda geometrických a UV dat je zaznamenaná v [detail-review.json](../review/ranger/detail-review.json). Konzole při závěrečné kontrole nevrátila chyby ani varování.

Offline kontrola navíc zahrnula všech devět srovnávacích tváří strážce, jeho tělo ze šesti směrů a sedm finálních renderů průzkumnice (tělo čelo/¾/bok/záda a tři pohledy na tvář). Přijaté opravy a přesné parametry jsou v [FACE.md](FACE.md) a [RANGER.md](RANGER.md). Zbývají malované přechody u vlasů a uší, jednoduchá geometrie boltce a možné kolize oděvu; tento záznam nepotvrzuje bezchybnost všech 214 klipů.

Po rozšíření hlav elfa a průzkumnice byly nové statické exporty prohlédnuty z čela, ¾, profilu a zezadu; tváře z čela, ¾ a profilu proti uloženým baseline a původnímu strážci. [Srovnávací stránka](../review/head-width.html) drží stejné kamery v rámci před/po obou nových postav. Ve skutečném browser vieweru byly na obou znovu přehrány idle, `Running A`, `Jog Fwd Loop`, `Sprint Loop`, `Jump Full Short` a `Waving`; u elfa také zobrazená kostra a detail tváře zepředu a z profilu. Přepnutí všech tří postav aktualizovalo počty, referenci a katalog; konzole neměla chyby ani varování. U elfa při běhu zůstává možný průnik pláště s nohama a na vlasové projekci v blízkém profilu zůstávají malované přechody. Tyto limity číselný PASS nepostihne.

## Co číselné kontroly nedokazují

Kvalita všech 214 klipů není ručně zkontrolována snímek po snímku. Extrémní pózy, sedání, lezení a boj potřebují hodnocení pro konkrétní scénu a rekvizity. Přehrání bez chyby není automaticky produkčně hotová animace.

- IK upravuje délky končetin, nemá kontakt s terénem ani automatické zamykání chodidel. Může zbýt skluz či průnik podlahou, zvlášť při odlišných proporcích nebo scéně.
- Zbroj má široké objemy. V extrémním ohybu se mohou pláty a tělo prolínat; není tu systém kolizí armor dílů.
- Tabard má 4 odvozené kosti, nikoli cloth simulaci nebo kolize s nohama.
- Rukavice mají celistvý objem a palec, nemají samostatně rigované prsty. Pohyby držení nástrojů/zbraní se přehrávají bez těchto rekvizit.
- KayKit spawn/disassembly efekty používající animované měřítko nebo rozpojování kostí nejsou kompletně reprodukovány; přenášíme především humanoidní pózu. Raw originály zůstaly přiložené.
- `KAY_Skeletons_Spawn_Ground` začíná ve zdroji pod zemí. Zachovaný pohyb rootu může mít během klipu rozsah přes 12 m, aniž se deformovaný model rozpadá. Tyto efekty potřebují scénu a nastavení kamery; ve standardním vieweru může postava opustit viditelný prostor.
- Cílové soubory používají vybranou in-place knihovnu; všechny dostupné původní root-motion soubory jsou uložené, ale nejsou duplicitně přidány do vieweru.
- Oprava tváře omezuje dvojité rysy a barevný šev. Ucho, jemné detaily a světlo jsou stále částečně namalované; model není sken ani mimický obličejový rig.

## Ruční kontrola po úpravě

Otevři viewer, vyber postupně všechny tři postavy a nech základní pohyby několikrát proběhnout. U strážce ověř idle, KayKit běh, Quaternius jog/sprint, skok a gesto; zapni kostru a scrubbuj krajní pózy. Zkontroluj ruce při běhu, kolena při skoku, ramena při gestu a pláty při předklonu.

Zepředu, ¾ a z boku v poli „Srovnání projekce“ přepínej aktuální model, výchozí stav projekce a historický obličej. Kamera musí zůstat stejná. Prohlédni také celé rameno, čelist u límce, vlasy ze strany a předloketí, aby na sousedním dílu nezůstalo cizí ucho, vous či kus zbroje. Přepni čistý tvar, aby textura nezakrývala chybu geometrie. Konzole nesmí mít chyby načítání nebo animation binding. Výsledek této browser kontroly zaznamenej samostatně; úspěšný HTTP požadavek ani numerické PASS ji nenahrazují.
