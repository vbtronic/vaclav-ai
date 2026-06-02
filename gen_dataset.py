# -*- coding: utf-8 -*-
import json, random, os

def ex(user, asst):
    return {"messages": [{"role": "user", "content": user}, {"role": "assistant", "content": asst}]}

DATA = [
ex("What is the Pythagorean theorem?",
   "Pythagorova veta rika, ze v pravoruhlém trojuhelniku plati:\n\n**a2 + b2 = c2**\n\nkde *c* je prepona (nejdelsi strana, naproti pravemu uhlu) a *a*, *b* jsou odvesny.\n\n**Priklad:** Trojuhelnik s odvesnami 3 cm a 4 cm:\n- 32 + 42 = 9 + 16 = 25\n- c = 5 cm\n\n*Zkus: jaka je prepona trojuhelniku s odvesnami 5 a 12?*"),

ex("how do i solve quadratic equation",
   "Kvadraticka rovnice ma tvar **ax2 + bx + c = 0**.\n\nResim ji pres diskriminant D = b2 - 4ac\n\n- D > 0: dva koreny x = (-b +- odmocnina(D)) / 2a\n- D = 0: jeden koren x = -b / 2a\n- D < 0: zadny realny koren\n\n**Priklad:** x2 - 5x + 6 = 0\n- D = 25 - 24 = 1\n- x1 = (5+1)/2 = 3, x2 = (5-1)/2 = 2\n\n*Zkus vyresit: x2 - 7x + 12 = 0*"),

ex("co je to elektron",
   "Elektron je zakladni casticka se **zapornym elektrickym nabojem**.\n\nVlastnosti:\n- Naboj: -1,6 × 10^-19 C\n- Hmotnost: 9,1 × 10^-31 kg (1836x lehci nez proton)\n- Objeha kolem jadra atomu\n\nElektrony zpusobuji:\n- Chemicke vazby\n- Elektricky proud\n- Svetlo z zarovky\n\n*Proc jsou elektrony zaporne a protony kladne? (Je to jen historicka konvence!)*"),

ex("vysvetli mi absolutni hodnotu",
   "Absolutni hodnota |x| rika, **jak daleko je cislo od nuly** na ciselne ose.\n\n- |5| = 5\n- |-5| = 5\n- |0| = 0\n\n**Geometricky:** |a - b| = vzdalenost bodu a a b.\n\n**Priklad:** Teplotni rozdil Praha (-3 C) a Brno (2 C):\n|-3 - 2| = |-5| = 5 stupnu\n\n**Rovnice:** |x - 3| = 5 -> x = 8 nebo x = -2\n\n*Zkus vyresit: |2x + 1| = 7*"),

ex("Mam hadanku: Je pondeli. Petr rika pravdu jen v pondeli, stredu a patek. Co rekne dnes?",
   "Rozeberu to krok za krokem:\n\n1. Dnes je pondeli\n2. Petr rika pravdu v pondeli, stredu a patek\n3. Pondeli je v seznamu -> Petr dnes **rika pravdu**\n\nPokud se ho zeptas 'Je dnes pondeli?', rekne: **Ano.**\n\nToto je priklad logiky vyroku - overujeme podminky, ne jen intuici.\n\n*Bonusova otazka: Co Petr rekne v utery na otazku 'Rikas dnes pravdu?'*"),

ex("logicka uloha: vsichni psi jsou savci. rex je pes. co z toho plyne?",
   "Tohle je klasicky **sylogismus**.\n\n- Premisa 1: Vsichni psi jsou savci (P -> S)\n- Premisa 2: Rex je pes (Rex je v P)\n- **Zaver: Rex je savec** (Rex je v S)\n\nTato forma se jmenuje *modus ponens* a je vzdy platna.\n\n**Pozor na chybu:** 'Rex je savec -> Rex je pes' NEPLATI! Rex muze byt kocka nebo velryba.\n\n*Zkus: Vsechna prvocisla vetsi nez 2 jsou licha. 7 je prvocislo vetsi nez 2. Co z toho plyne?*"),

ex("co je to induktivni uvazovani",
   "Induktivni uvazovani jde **od konkretnich prikladu k obecnemu pravidlu**.\n\n**Priklad:**\n- Labut 1 je bila\n- Labut 2 je bila\n- Labut 3 je bila\n- Zaver: Vsechny labute jsou bile.\n\n**Problem:** V roce 1697 Evropane objevili v Australii cerne labute - a teorie se zhroutila!\n\n**Rozdil od dedukce:**\n- Dedukce: z obecneho vyvozuji konkretni (vzdy platne)\n- Indukce: z konkretnich vyvozuji obecne (pravdepodobne, nikdy 100%)\n\n*Vymysli priklad induktivniho uvazovani z kazodenniho zivota.*"),

ex("3 muzi potrebuji 3 hodiny na vykopani 3 der. kolik hodin potrebuje 1 muz na 1 diru?",
   "Tohle je klasicka past - intuice rika 1 hodinu, ale overme to:\n\n- 3 muzi × 3 hodiny = 9 clovekohodin celkem\n- Na 3 diry -> 9 / 3 = **3 clovekohodiny na 1 diru**\n\n**Odpoved:** 1 muz potrebuje **3 hodiny** na 1 diru.\n\nProc intuice klame? Muzi kopali *paralelne*, kazdy svou diru cele 3 hodiny.\n\n*Nova otazka: Kolik muzu by potrebovalo 1 hodinu na 6 der?*"),

ex("co je to paradox lhare",
   "Paradox lhare: **'Tato veta je nepravdiva.'**\n\n- Pokud je pravdiva -> rika pravdu -> je nepravdiva. Spor!\n- Pokud je nepravdiva -> to co rika neplati -> je pravdiva. Spor!\n\nVeta nema konzistentni pravdivostni hodnotu.\n\n**Proc je to dulezite?** Kurt Godel (1931) pomoci podobnych argumentu dokazal, ze v kazdem dostatecne silnem formalnim systemu existuji pravdive vety, ktere nelze dokazat (vety o neuplnosti) - jeden z nejvyznamnejsich vysledku matematiky.\n\n*Znas jiny sebereferencni paradox?*"),

ex("jak se lisi privlastek shodny a neshodny",
   "Oba rozviji podstatne jmeno, ale lisi se zpusobem pripojeni.\n\n**Privlastek shodny:**\n- Shoduje se v padu, cisle a rode\n- Obvykle pridavne jmeno nebo zajmeno\n- Priklady: cervena ruze, moje kniha, treti misto\n\n**Privlastek neshodny:**\n- Nestride se - je ve fixnim tvaru\n- Priklady: dum ze dreva, chut k praci\n\n**Jak je rozeznat?** Zmen pad ridiciho slova:\n- cervena ruze -> cervene ruze (zmenil se -> shodny)\n- dum ze dreva -> domu ze dreva (zustal -> neshodny)\n\n*Urci privlastek: 'Stary muz z vedlejsi vesnice prinesl kosik plny jablek.'*"),

ex("co je podmět a přísudek, příklad",
   "Podmět a přísudek jsou základní větné členy.\n\n**Podmět:** kdo nebo co děj vykonává\n- Otázka: Kdo? Co?\n- Bývá v 1. pádu\n- Příklad: *Petr* běží. -> Petr je podmět\n\n**Přísudek:** co podmět dělá nebo jaký je\n- Nejčastěji sloveso\n- Příklad: Petr *běží.* -> běží je přísudek\n\n**Typy přísudku:**\n1. Slovesný: Jana čte.\n2. Jmenný se sponou: Jana je chytrá.\n3. Složený: Jana začala číst.\n\n*Urči podmět a přísudek: 'Tiché moře se lesklo pod hvězdami.'*"),

ex("vysvetli mi shodu prisudku s podmetem",
   "Prisudek se prizpusobuje podmětu v osobe, cisle a rode.\n\n**Muzsky zivotny rod -> -i**\nChlapci přišli. Muži seděli.\n\n**Ostatni rody -> -y nebo -a**\nDívky přišly. Města stála.\n\n**Vice podmetu ruzneho rodu:**\nPokud je aspon jeden muzsky zivotny -> muzsky zivotny rod:\nJan a Marie přišli. (Jan = muz. ziv. -> -i)\n\n**Caste chyby:**\n- SPATNE: Deti si hrali.\n- SPRAVNE: Deti si hraly. (deti = stredni rod)\n\n*Oprav: 'Zaci a zakyně seděly v lavicich.'*"),

ex("co byl Jan Hus a proc je dulezity",
   "Jan Hus (asi 1369-1415) byl cesky teolog, kazatel a reformator.\n\n**Kdo byl?**\n- Rektor Karlovy univerzity\n- Kazatel v Betlemske kapli (kazal cesky, ne latinsky)\n- Kritik korupce cirkve - prodavani odpustku, hromadeni majetku\n\n**Co prosazoval?**\n- Cirkev ridici se Pismem\n- Prijimani pod oboji pro laiky\n\n**Proc zemrel?** Na Kostnickém koncilu (1415) odmitl odvolat sve nazory a byl upalen 6. cervence 1415.\n\n**Proc je dulezity?**\n- Spustil husitske hnutí a husitske valky\n- Predchudce evropske reformace (Luther prisel o 100 let pozdeji)\n- 6. cervence je statni svatek CR\n\n*Proc si myslis, ze Hus odmitl odvolat sve nazory, i kdyz vedel, ze ho upalí?*"),

ex("co je to metafora, prirovnani, personifikace",
   "Tri zakladni basnicke figury.\n\n**Metafora:** prenasi pojmenovani na zaklade podobnosti BEZ 'jako'\n- Priklad: 'More hvezd se rozlilo po nebi.'\n\n**Prirovnani:** porovnava dve veci SE slovem 'jako' nebo 'jak'\n- Priklad: 'Byl statecny jako lev.'\n\n**Personifikace:** pripisuje lidske vlastnosti neživym vecem\n- Priklad: 'Viter si zpiVal v korunach stromu.'\n\n| Figura | Klic | Priklad |\n|--------|------|---------|\n| Metafora | bez 'jako' | more hvezd |\n| Prirovnani | se 'jako' | rychly jako blesk |\n| Personifikace | lidske vlastnosti | hory mlcely |\n\n*Najdi v Maji jednu metaforu a jednu personifikaci.*"),

ex("jak funguje fotosynteza",
   "Fotosynteza je proces, pri kterem rostliny premenuji svetlo na chemickou energii.\n\n**Rovnice:**\n6 CO2 + 6 H2O + svetlo -> C6H12O6 + 6 O2\n\n**Kde probiha?** V chloroplastech - zelenych organelach listu. Chlorofyl absorbuje cervene a modre svetlo (zelene odrazi).\n\n**Dve faze:**\n1. Svetelna faze: zachyti fotony, rozlozi vodu, uvolni kyslik\n2. Calvinuv cyklus: zabuduje CO2 do glukozy\n\n**Proc je dulezita?**\n- Produkuje kyslik, ktery dychame\n- Zaklad potravniho retezce\n\n*Proc listy na podzim zloutnou? Co se deje s chlorofylem?*"),

ex("co je to Newtonuv druhy zakon",
   "Newtonuv druhy zakon pohybu: **F = m * a**\n\n- F = sila [Newton, N]\n- m = hmotnost [kg]\n- a = zrychleni [m/s2]\n\n**Intuice:**\n- Vetsi sila -> vetsi zrychleni\n- Tezsi teleso -> mensi zrychleni pri stejne sile\n\n**Priklad:** Auto 1000 kg, sila 3000 N:\na = 3000 / 1000 = **3 m/s2**\n\nZa 1 sekundu dosahne rychlosti 3 m/s = 10,8 km/h.\n\n*Kdyz by motor pusobil stejnou silou na auto 500 kg, jake by bylo zrychleni?*"),

ex("jak funguje gravitace",
   "Gravitace pritahuje telesa s hmotnosti k jinym telesum s hmotnosti.\n\n**Newtonuv zakon:** F = G * m1 * m2 / r2\n\n- G = 6,67 × 10^-11 Nm2/kg2\n- Klesa se ctvercem vzdalenosti (2x dal -> 4x slabsi)\n- Pusobi na libovolnou vzdalenost\n\n**Einsteinova oprava (1915):** Gravitace je zakriveni prostoru a casu - hmotna telesa ohybaji prostorocas.\n\n**Priklady:**\n- Obeh Zeme kolem Slunce\n- Príliv (zpusobuje Mesic)\n- Cerne diry\n\n*Proc astronauti ve vesmirne stanici 'plavou'? Je tam gravitace, nebo ne?*"),

ex("jak vypocitam obvod a obsah kruhu",
   "Kruh ma polomer r (vzdalenost od stredu k obvodu).\n\n**Obvod:** o = 2 * pi * r (nebo pi * d, kde d = prumer)\n\n**Obsah:** S = pi * r2\n\n**pi = 3,14159...**\n\n**Priklad** r = 5 cm:\n- Obvod: 2 * 3,14 * 5 = 31,4 cm\n- Obsah: 3,14 * 25 = 78,5 cm2\n\n**Pametnka:**\n- Obvod: jdes kolem kruhu -> linearne (r na 1)\n- Obsah: vyplnujes plochu -> kvadraticky (r na 2)\n\n*Pizza o prumeru 30 cm vs. dve pizzy o prumeru 15 cm. Ktera nabizi vic testa?*"),

ex("co je to funkce v matematice",
   "Funkce je pravidlo, ktere kazde vstupnimu cislu x priradi prave jedno vystupni cislo y.\n\n**Zapis:** f(x) = 2x + 1\n- f(3) = 7\n- f(-1) = -1\n- f(0) = 1\n\n**Dulezite pojmy:**\n- Definicni obor (D): cisla, ktera smim vlozit\n- Obor hodnot (H): cisla, ktera mohou vyjit\n- Graf funkce: vizualni zobrazeni\n\n**Typy:**\n- Linearni: f(x) = kx + q -> primka\n- Kvadraticka: f(x) = ax2 + bx + c -> parabola\n- Exponencialni: f(x) = a^x -> rychly rust\n\n*Jaky je definicni obor funkce f(x) = 1/x? Proc?*"),

ex("co je to promenna v programovani",
   "Promenna je **pojmenovane misto v pameti**, kde si program uklada hodnotu.\n\nPredstav ji jako krabicku s napistkou - napistka je nazev, obsah je hodnota.\n\n**Priklad v Pythonu:**\n```python\nvek = 15\njmeno = 'Jana'\nje_student = True\n```\n\n**Typy hodnot:**\n- int: cele cislo (15, -3)\n- float: desetinne (3.14)\n- str: text ('ahoj')\n- bool: True / False\n\n**Proc jsou uzitecne?** Program pracuje s libovolnymi hodnotami:\n```python\ncena = 100\nsleva = 20\nzaplatit = cena - sleva  # = 80\n```\n\n*Zkus napsat promenne pro vypocet obvodu obdelniku (sirka=5, vyska=3).*"),

ex("vysvetli mi co je binarni soustava",
   "Binarni soustava ma **zaklad 2** - pouziva jen 0 a 1.\n\nProc ji pocitace pouzivaji? Tranzistor ma dva stavy: zapnuto (1) a vypnuto (0).\n\n**Jak cist binarni cislo?**\nKazda pozice je mocnina 2:\n```\n1 0 1 1\n8 4 2 1\n```\n1*8 + 0*4 + 1*2 + 1*1 = 11\n\n**Prevod 11 -> binarni:**\n11 / 2 = 5 zbytek 1\n5 / 2 = 2 zbytek 1\n2 / 2 = 1 zbytek 0\n1 / 2 = 0 zbytek 1\nZdola nahoru: **1011**\n\n**Zajimavosti:**\n- 1 bit = jedna 0 nebo 1\n- 8 bitu = 1 byte\n- 1 KB = 1024 bytu\n\n*Zkus prevest cislo 13 do binarni soustavy.*"),

ex("jak se nejlepe ucit",
   "Veda o uceni ma jasne zavery:\n\n**Co funguje:**\n\n1. **Rozlozene opakovani** - misto biflování den pred testem opakuj v rozestupech: dnes -> za 2 dny -> za tyden. Aplikace Anki je skvela.\n\n2. **Aktivni vybavovani** - misto cteni zapisku se sam sebe zkousej. Zakryj zapisky a zkus si vybavit obsah. Funguje 2x lepe nez pasivni cteni.\n\n3. **Prokladane uceni** - michej ruzna temata. Mozek se uci lepe kdyz musi rozlisovat.\n\n4. **Elaborativni dotazovani** - ptej se 'Proc to tak je?' a 'Jak to souvisi s tim, co uz vim?'\n\n**Co nefunguje:**\n- Prepisovani zapisku (pasivni)\n- Podtrhovani (falesny pocit uceni)\n- Uceni ve velkych blocich\n\n**Technika Pomodoro:** 25 minut uceni -> 5 minut prestávka\n\n*Zkus tento tyden aktivni vybavovani misto cteni zapisku.*"),

ex("co je to kriticke mysleni",
   "Kriticke mysleni je schopnost **hodnotit informace nezaujate** - nehledat potvrzeni toho, co uz verim, ale hledat pravdu.\n\n**Zakladni kroky:**\n1. Identifikuj tvrzeni - je to fakt, nebo nazor?\n2. Ptej se na dukazy - jaky je zdroj? Je spolehlivy?\n3. Hledej alternativy - existuje jine vysvetleni?\n4. Uvědom si zkresleni - konfirmacni zkresleni: tendence hledat jen to, co potvrzuje nas nazor\n\n**Priklad:**\nTvrzeni: 'Cokolada pomaha pri uceni.'\n- Kdo to tvrdi? (Cokoladovna nebo vedci?)\n- Jaka studie? (Kolik lidi, jak kontrolovana?)\n- Existuji protistudie?\n\n*Zkus aplikovat na zpravy, ktere dnes vidis na internetu.*"),

ex("vysvetli Einsteinovu teorii relativity jednoduse",
   "Einstein prinesl dve revoluce:\n\n**Specialni teorie relativity (1905):**\nDve klicove myslenky:\n1. Fyzikalni zakony jsou stejne pro vsechny pozorovatele v rovnomernem pohybu\n2. Rychlost svetla je vzdy stejna (300 000 km/s), bez ohledu na pohyb zdroje\n\nDusledky:\n- Cas plyne pomaleji pro pohybujici se telesa (dilatace casu)\n- Rychle pohybujici se teleso je kratsi (kontrakce delky)\n- E = mc2: hmotnost a energie jsou teze vec\n\n**Obecna teorie relativity (1915):**\n- Gravitace neni sila, ale zakriveni prostoru a casu\n- Hmotna telesa ohybaji prostorocas kolem sebe\n- Svetlo se ohyba v gravitacnim poli\n\n*Proc si myslis, ze je rychlost svetla omezeni? Co by se stalo, kdybys letěl rychleji nez svetlo?*"),

ex("jak dokazat matematicky vyrok",
   "Matematicky dukaz je logicky argument, ktery ukazuje, ze tvrzeni musi byt pravdive.\n\n**Hlavni metody:**\n\n**1. Primy dukaz**\nZ premis logicky odvozujeme zaver.\nPriklad: Dokaž, že soucet dvou sudych cisel je sude.\n- Sude cislo = 2k pro nejake celo k\n- 2a + 2b = 2(a+b) = sude\n\n**2. Dukaz sporem (reductio ad absurdum)**\nPredpokladas opak a dojdes ke sporu.\nPriklad: Dokaž, že odmocnina z 2 je iracionalni.\n- Predpoklej sqrt(2) = p/q (v základnim tvaru)\n- Pak 2 = p2/q2, tedy p2 = 2q2\n- p2 je sude -> p je sude -> p = 2m\n- (2m)2 = 2q2 -> q2 = 2m2 -> q je sude\n- Spor: p i q jsou sude, ale zlomek mel byt v zakladnim tvaru!\n\n**3. Matematicka indukce**\nProverit pro n=1, pak ukazat ze plati pro n -> n+1.\n\n*Zkus dokazat: soucet prvnich n cisel = n*(n+1)/2*"),

ex("co je to algoritmicke mysleni",
   "Algoritmicke mysleni je schopnost resit problemy jako **sekvenci presnych kroku**.\n\nAlgoritmus je postup, ktery:\n1. Ma jasne definovany vstup a vystup\n2. Skladа se z konecneho poctu kroku\n3. Kazdy krok je jednoznacny\n4. Vzdy skonci\n\n**Priklad: Algoritmem najdi nejvetsi cislo v seznamu**\n```\n1. Nastav maximum = prvni cislo\n2. Pro kazde dalsi cislo v seznamu:\n   - Pokud je vetsi nez maximum:\n     -> nastav maximum = toto cislo\n3. Vrat maximum\n```\n\n**Klicove koncepty:**\n- Sekvence: kroky za sebou\n- Podminka: if/else\n- Cyklus: opakuj dokud...\n- Funkce: pojmenovany blok kroku\n\n*Navrhni algoritmus pro razeni 3 cisel od nejmensiho po nejvetsi.*"),
]

random.seed(42)
random.shuffle(DATA)

split = int(len(DATA) * 0.88)
train = DATA[:split]
valid = DATA[split:]

os.makedirs("data", exist_ok=True)

with open("data/train.jsonl", "w", encoding="utf-8") as f:
    for ex_ in train:
        f.write(json.dumps(ex_, ensure_ascii=False) + "\n")

with open("data/valid.jsonl", "w", encoding="utf-8") as f:
    for ex_ in valid:
        f.write(json.dumps(ex_, ensure_ascii=False) + "\n")

print(f"Train: {len(train)} prikladu")
print(f"Valid: {len(valid)} prikladu")
print("Ulozeno do data/train.jsonl a data/valid.jsonl")
