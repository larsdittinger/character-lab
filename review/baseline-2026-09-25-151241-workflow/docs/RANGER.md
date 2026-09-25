# Druhá kalibrace: měděnovlasá průzkumnice

Průzkumnice je samostatný druhý test rekonstrukce. Má nový referenční obrázek, nově odečtené siluety, jiné proporce, vlastní atlas, skutečně přizpůsobenou kostru a stejných 214 stažených zdrojových pohybů. Není to textura rytíře přelepená na původní geometrii.

## Původ reference

Jedno volání vestavěného `image_gen` vytvořilo **jeden obrázek 1536 × 1024 obsahující tři pohledy**. Gemini se pro tento charakter nevolalo. Neuvádíme skutečnou cenu ani odhad faktury. Původní neměnný výstup je [turnaround.png](../references/ranger/turnaround.png); úplný prompt, původ a SHA-256 jsou v [turnaround.json](../references/ranger/turnaround.json) a [ranger-prompt.txt](../config/ranger-prompt.txt).

## Reprodukce offline

Používá lokální `.venv`, `requirements.txt`, `node_modules` a stejný Blender jako rytíř. Referenci ani zdrojové archivy není třeba znovu generovat/stahovat.

```sh
.venv/bin/python tools/ranger_pipeline.py build
.venv/bin/python tools/ranger_pipeline.py render
npm run serve
```

Viewer: `http://localhost:8770/`, volba **Lesní průzkumnice**. Samostatné kroky jsou `geometry`, `rig`, `motion`, `validate`, `render`. Změna geometrie nebo projekce vyžaduje nový `build`, protože GLB obsahuje vložený atlas. Pipeline zastaví i Python chybu uvnitř Blenderu (`--python-exit-code 1`).

| Výstup | Obsah |
|---|---|
| `assets/ranger-static.glb` / `.blend` | Statický model, v Blenderu 29 oddělených uzavřených dílů |
| `assets/ranger-rigged.glb` / `.blend` | Nově fitovaná kostra a váhy; v Blenderu oddělené díly |
| `assets/ranger-animated.glb` / `.blend` | 214 klipů / 214 Blender actions, při otevření aktivní idle |
| `animations/ranger/retargeted/` | 214 malých GLB pro tuto konkrétní ranger hierarchii, bez mesh a textury |
| `animations/ranger/catalog.json` | Zdrojový název, balík, délka a parametry každého klipu |
| `review/ranger/validation.json` | Skutečný strojový výsledek kontrol |

Sdílené retarget/export/validate skripty vybírají výstup explicitně pomocí `CHARACTER_LAB_CHARACTER=knight|ranger`. Ranger wrapper nemění text ani algoritmus společných skriptů. Anatomická korekce A/T-pózy, hip-relative IK a původní zdrojové křivky zůstávají stejné; cílové klouby a délky končetin jsou nové.

## Co se muselo nově odečíst

Konfigurace [ranger-profiles.json](../config/ranger-profiles.json) obsahuje hlavní měřítko a profily dílů. Střed čela X=317, hloubkový počátek bočního pohledu X=773, střed zad X=1220, koruna Y=17, zem Y=959; autorská výška 2.5 m. Měřítko je `2.5 / 942`. Y je nahoře, +Z dopředu. [ranger-rig.json](../config/ranger-rig.json) ukládá nově odečtené anatomické body v metrech.

Párové díly průzkumnice jsou odečtené na pravé straně čelního obrázku, což je **anatomická levá strana, +X, suffix L**. Rytíř má výchozí odečty na opačné straně obrázku. Převzetí stejného pojmenování bez této kontroly původně přiřadilo končetiny protějším kostem: numerický skin test prošel, ale idle v browseru se viditelně deformoval. Finální model má názvy opravené a rig před přiřazením vah zastaví build, pokud centroid párového dílu L neleží na +X nebo R na −X. Výchozí silueta sama tuto chybu neodhalí; rozhodující je skutečné přehrání pohybu.

Reference má konzistentní identitu, ale její tři siluety nejsou přesně shodné. Proto má hlava navíc `rearHeadRegistration`: zvláštní tabulku šířek zadního pohledu podle výšky. Pouhé zrcadlení stejného pixelového X z předku do zad promítalo šedé pozadí do horní části účesu. Boční obličej má samostatně zarovnané výšky očí, nosu, úst a brady a malou hloubkovou korekci.

První experiment s odděleným objemem účesu vytvořil překryv na čele. Finální varianta používá jednu souvislou hlavu včetně kštice. Historické kontrolní rendery zůstávají v `review/ranger/face-first-3q.png` a `face-first-side.png`. Aktuální `face-front.png`, `face-3q.png`, `face-side.png` pocházejí z exportovaného statického GLB a shodného nastavení kamery a světel.

## Vlastnictví projekce

- Uši mají dva samostatné uzavřené objemy připojené k hlavě. Jejich přední a boční plocha vzorkuje odpovídající část reference; kůže pod uchem nevytváří další ostré ucho.
- Ramenní díly nepoužívají boční projekci přes zakrytý krk nebo hlavu. Detail je z čela a zad; nepozorovaný bok má odvozenou barvu kůže/zbroje, nikoli obraz cizí anatomie.
- Účes má pro hranice masku skutečných měděných vlasů. Chybějící okrajové vzorky doplňují nejbližší platné vlasové pixely; bílé/šedé pozadí ani pleť nepřebírají barvu celé kštice. Je to vycpání projekčního okraje, nikoli další generovaný obrázek.
- Horní kalhoty jsou v předloze zakryté tunikou. Používají tedy autorskou tmavou látku, pokračují až pod pás a bok zakrývá samostatný kožený díl. Oříznutá plochá horní hrana se tím neukazuje pod pasem.
- Atlas má 2000 × 3168 pixelů s výplní okrajů UV ostrovů.

### Cílená oprava ucha a límce, ověřená před/po

Výchozí stav této poslední úpravy je zachován jako `assets/ranger-before-detail.glb`. Snímky čelo/¾/profil i kopie původního `ranger_model.py` a profilů jsou v `review/ranger/baseline-resume/`. [Šest srovnávacích renderů](../review/ranger/detail-comparison.html) ukazuje stejnou geometrii a stejné kamery před a po opravě.

Příčina zbytku druhého ucha byla konkrétní: stará obdélníková maska odstranila střed ucha z projekce hlavy, ale vynechala světlý horní oblouk. Ostrá hrana obdélníku současně vytvořila hnědý pás u kořene samostatného ušního dílu. Oprava je v `tools/ranger_model.py`, v části výběru platných zdrojových barev:

1. **Čelní ucho na hlavě:** dvě měkké eliptické masky mají středy `(365,108)` a `(269,108)` px, poloměry `(13,23)` px. Normalizovaný poloměr přechází přes `smooth((radius-.85)/.28)`. Zakrytou oblast doplňuje sousední platný povrch v X=351, resp. 283 při stejné výšce. Samostatné ušní meshe nadále dostávají skutečnou texturu ucha.
2. **Boční ucho na hlavě:** střed `(779,105)`, poloměry `(17,23)` px; maska `1-smooth((radius-.84)/.30)` zahrnuje i horní oblouk. Výplň plynule přechází mezi okolní kůží a vlasy: kůže se vzorkuje poblíž X=755, vlasy poblíž X=806 z platné vlasové oblasti. Převaha vlasů se mění podle hloubky X=774–787 a výšky Y=89–101. Nejde o rozmazání celého obličeje ani oka, ale o odstranění cizího ostrého rysu z povrchu pod skutečným uchem.
3. **Límec:** dřívější konstantní X=790 protahovalo jediný sloupec reference kolem krku a kreslilo vodorovný pruh. Finální projekce opět vzorkuje skutečné dvourozměrné `(profileX,imageY)`. Viditelný boční obrys má řádky `[145,745,804]`, `[153,749,808]`, `[161,751,813]`, `[175,743,820]`, `[190,731,826]`, `[205,719,829]`; vzorek zůstává 3 px uvnitř intervalu. Světlý krémový lem je platný materiál, a proto se na krku nepovažuje za šedé studiové pozadí.

Výsledek porovnání: v ¾ a profilu zmizel světlý náznak druhého ucha, napojení nemá původní tvrdý obdélníkový pás a krémový lem límce sleduje diagonální tvar z reference. Čelní oči, ústa, proporce, kostra a váhy zůstaly stejné. Tento výsledek byl zvolen po porovnání všech tří kamer; další experimenty se do dodaného stavu nepřidávaly.

Pro dalšího agenta: nejprve zachovej GLB a tři staré rendery, pak oprav konkrétní vlastnictví zdrojového rysu. Nepoužívej tyto pixelové masky na nový obrázek bez nového měření. Po změně spusť celý `ranger_pipeline.py build`, potom `ranger_pipeline.py render`, porovnej čelo/¾/profil a v browseru znovu načti animovaný GLB, aby nezůstala stará vložená textura v cache. `validate` kontroluje finální model i 214 odpovídajících motion-only souborů; vzhled napojení ucha musí posoudit člověk/agent z renderů.

## Naměřené kontroly

Finální GLB: **57 584 trojúhelníků, 29 477 vertexů, 27 skin joints, 214 klipů**. Blender zachovává 29 dílů ve statickém/rigged souboru a 214 actions v animovaném souboru. Všech 29 dílů má 0 otevřených a 0 non-manifold hran. K dispozici zůstává 32 skutečných idle klipů a 8 běhů.

Validator vyhodnotil 1284 póz se skutečným skinningem, ověřil normalizované váhy a quaterniony, konečné hodnoty, rostoucí časy a shodu všech 214 samostatných motion souborů s kompletním GLB. Maximální odchylka součtu vah je přibližně `2.98e-8`, quaternionu `4.70e-8`, IK kotníku `9.87e-6 m`. Největší prostorový rozsah jedné vyhodnocené pózy je přibližně 2.94 m.

Druhý model odhalil chybu staré kontroly: součet rozsahu **celé trajektorie** zaměňovala za rozpad mesh. Zdrojový KayKit skeleton spawn přichází z hloubky pod zemí a pro delší nohy průzkumnice překračuje 12 m celkového cestování. Opravená společná kontrola měří velikost skutečně deformované postavy **v každé póze** a zvlášť reportuje trajektorii. Zdrojový pohyb nebyl vystřižen ani nahrazen domácí animací.

## Vizuální výsledek a limity

### Korekce proporce hlavy po srovnání se strážcem

Při společné kontrole nového elfa a průzkumnice upozornil uživatel, že obě hlavy v celotělovém pohledu působí úzce. Před změnou byly GLB, profil, skript, atlas a všechny dosavadní kontrolní rendery uložené do `review/ranger/baseline-2026-09-25-head-width/`. V [ranger-profiles.json](../config/ranger-profiles.json) je nyní `headWidthScale: 1.10`; [ranger_model.py](../tools/ranger_model.py) rozšiřuje X souřadnice hlavního dílu tváře, posouvá samostatné uši o odpovídající vzdálenost a rozšiřuje krk o polovinu korekce. Zdrojové souřadnice očí, úst, vlasů a UV atlasu zůstávají měřené z téže předlohy.

Maximální šířka tváře se změnila z **0,311 m na 0,342 m**. [Srovnání stejných kamer](../review/head-width.html) zachycuje čelo, ¾, profil a celé tělo před/po vedle původního strážce. Po změně proběhl `ranger_pipeline.py geometry`, render, `rig`, `motion` a `validate`; finální validace zůstává PASS se 57 584 trojúhelníky, 29 477 GLB vertexy, 27 kostmi, 214 klipy, 214 motion-only soubory a 214 Blender actions. Ve vieweru byly opět prohlédnuty idle, KayKit běh, Quaternius jog/sprint, skok a gesto; konzole byla bez chyb. Pro další postavu je třeba udělat stejné vizuální srovnání hlavy **před** přenosem 214 animací. Jediný číselný poměr nenahradí úsudek o stylizaci.

Statické kontrolní rendery pokrývají tělo z čela, ¾, boku a zad a obličej ze tří úhlů. Změny účesu, uší a bočních ploch se kontrolovaly na skutečném exportu, ne jen na zdrojovém obrázku. Výrazný druhý ušní oblouk a vodorovný pruh límce jsou opravené, ale tento experiment není filmově čistý obličejový model: jemné stínování a natažení malované barvy u kořene ucha či v účesu jsou při velkém detailu stále patrné. Ucho je jednoduchý uzavřený loft, nikoli anatomická retopologie boltce. Zdrojové světlo je součástí namalované textury. Malá tvář v jednom celotělovém sheetu omezuje rozlišení očí.

Rukavice nemají jednotlivé prsty ani mimiku. Sukně má jednoduché kosti, nikoli cloth kolize; širší kožené boky a paže mohou při extrémních gestech procházet tělem. Numeric PASS neověřuje produkční kvalitu každého snímku všech 214 klipů. Ověření konkrétního boje, sezení nebo práce vyžaduje rekvizity, scénu a kontrolu kontaktu chodidel. Reference a její nové měření dokazují druhou samostatnou kalibraci, nikoli univerzální automatický převod libovolného PNG na hotovou postavu.
