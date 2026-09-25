# Přechod obličeje a vlastnictví projekce

Původní textura zobrazovala druhý náznak oka a obočí na spánku. Zarovnání rysů a objem tváře tuto chybu omezily. Další kontrola odhalila jiný problém: **ucho na vršku nárameníku a zlatý okraj zbroje na čelisti**. Rozmazání tuto chybu neopraví. Zdrojový pixel musí nejdřív patřit správné části postavy.

## Zarovnání tváře

1. **Objem tváře.** Exponent průřezu 1.65, 100 výškových vzorků před redukcí a drobný reliéf nosu, očního okolí a rtů.
2. **Výškové zarovnání.** Čelní oko Y=165 odpovídá profilu Y=162, nos 194→190, ústa 216→213 a spodní brada 258→255.
3. **Hloubkové zarovnání.** Posun bočního vzorku závisí na výšce: u očí +7 px, u nosu +8 px, u brady klesá k nule.
4. **Oddělení detailu a barvy.** Laplaceova pásma s poloměry 0, 1.5, 5 a 16 px používají užší přechod pro ostré rysy a širší pro barvu.

Tato nastavení zůstávají v `config/face.json`. Aktuální oprava nemění geometrii, kostru ani původní měření `config/profiles.json`.

## Oprava přesahu mezi díly

`config/projection.json` nově popisuje viditelné oblasti předlohy **odděleně od hloubkového tvaru geometrie**. Řádky jsou `[imageY, povolenéLevéX, povolenéPravéX]`. Oblasti mohou mít také vyloučené polygony.

Konkrétní chyba: první hloubkový řez nárameníku v Y=182 používá X=1188–1240. V této části bočního obrázku je ale ucho. Skutečně viditelná zlatá zbroj začíná až přibližně na X=1242. Podobně v Y=231 končí viditelný vous přibližně na X=1156; dále už je rameno, nikoli čelist.

- **Nárameníky a předloktí:** pixely patřící uchu, vousům, rukávu nebo rukavici mají nulovou váhu bočního zdroje. Nahradí je čelní projekce stejného dílu. Na platné straně hranice je úzký přechod.
- **Čelist:** boční souřadnice jsou omezené na skutečně viditelnou tvář a vous. V zakryté oblasti se pokračuje nejbližším platným materiálem.
- **Zadní vlasový díl a zátylek:** obdobně čerpají jen z vlasů; profilový nárameník ani zadní límec se na hlavu nepřenášejí.
- **Bezpečný okraj:** vzorkování drží 2 px odstup od hranice, přechod má šířku 3 px. Nejde o plošné rozmazání předlohy.

Skrytá část tváře tím není anatomicky rekonstruována. Pokračování vousu/vlasu je řízená výplň nezobrazeného povrchu. Ucho strážce stále zůstává převážně v textuře; nový test hraničářky má samostatné ušní díly.

`review/projection.json` zaznamenává 9 kontrol známých chybných souřadnic, počty odmítnutých/upravených vzorků a zbývající váhu zakázaného bočního zdroje. Tyto kontroly prokazují dodržení uložených masek, nikoli správnost každého ručně odečteného pixelu. Zdroj je navíc svázán s uloženým otiskem, aby výměna obrázku neaplikovala staré masky potichu.

## Porovnání

Ve vieweru vyber klidovou pózu, detail tváře a v poli **Srovnání projekce** přepínej aktuální stav, stav před opravou projekce nebo historickou tvář. Kamera při přepnutí zůstává stejná.

| Pohled | Před opravou přesahů | Aktuální |
|---|---|---|
| Čelo | ![Před čelo](../review/face-baseline-front.png) | ![Po čelo](../review/face-after-front.png) |
| Tři čtvrtiny | ![Před ¾](../review/face-baseline-3q.png) | ![Po ¾](../review/face-after-3q.png) |
| Profil | ![Před profil](../review/face-baseline-side.png) | ![Po profil](../review/face-after-side.png) |

[Stránka s přepínatelným srovnáním](../review/faces.html) zahrnuje i historické zdvojení rysů. `assets/knight-before-projection.glb` je stav před aktuální opravou; `assets/knight-before-face.glb` zachovává původní tvář. `tools/render_faces.py` vyrenderuje všech **9 obrázků**: historický stav, výchozí stav této iterace a aktuální model, vždy čelo/¾/profil.

## Jak postup opakovat

Nejdřív zarovnej oči, nos, ústa a bradu. Na neotexturovaném tvaru ověř siluetu ze tří pohledů. Pro každý díl označ, kde je v daném obrázku skutečně vidět; hloubkový obrys tuto informaci nenahrazuje. Teprve potom určuj přechod mezi platnými zdroji a míchej barvu. Jeden viditelný bok má mít jedno oko, jedno obočí a jedno ucho. Zkontroluj také cizí barvy na sousedních dílech, zejména čelist/límec, ucho/rameno a rukáv/předloktí.

Pro nový obrázek znovu odečti geometrii, korespondence i masky. Pouhá výměna PNG není nové modelování. Pro filmový detail by následovala retopologie obličeje, samostatné oči a kontrolované albedo bez namalovaného světla.

## Technické podklady

Oddělení výběru platného zdrojového pohledu od vyrovnání švů odpovídá obecnému principu popsanému v práci [Waechter, Moehrle a Goesele: Let There Be Color!](https://download.hrz.tu-darmstadt.de/pub/FB20/GCC/paper/Waechter-2014-LTB.pdf). Zde používáme ručně naměřené masky, nikoli jejich automatický fotogrammetrický algoritmus. Okrajová výplň UV ostrovů omezuje švy při filtraci a mipmappingu, jak popisuje [Blender Manual: Render Baking / Margin](https://docs.blender.org/manual/en/latest/render/cycles/baking.html); samotná výplň neopravuje nesprávně zvolený obsah obrázku.
