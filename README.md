# 2048 AI

Schoolproject AI Programming (VIVES Brugge, Elektronica-ICT, 2026-2027).

We maken het spel 2048, maar dan speelt een AI het zelf. Voor elke zet kijkt de AI vooruit naar wat er kan gebeuren, inclusief de willekeurige nieuwe tegel, en kiest daarna de beste zet.

## Wie doet wat

<img src="https://github.com/LarsYse.png" width="24" align="center"> **[Lars Ysebaert](https://github.com/LarsYse)**: interface (het spel op het scherm tonen)

<img src="https://github.com/Oceandek.png" width="24" align="center"> **[Ocean Dekeyser](https://github.com/Oceandek)**: main (spelregels, bord en alles aan elkaar koppelen)

<img src="https://github.com/Brent69420809.png" width="24" align="center"> **[Brent Vileyn](https://github.com/Brent69420809)**: algoritme (de AI die de beste zet kiest)

## Starten

Je hebt enkel Python 3 nodig, er zijn geen extra pakketten nodig.

```
python main.py              # start de website, er opent vanzelf een tabblad in je browser
python main.py terminal     # zelf spelen in de terminal met z/q/s/d (x = stoppen)
```

De website draait op `http://localhost:8000`. Stoppen doe je met `Ctrl+C` in de terminal.

## Gamemodes

- **Singleplayer**: je speelt alleen en probeert de 2048-tegel te halen. Je kan een zet ongedaan maken.
- **Tegen de bot**: jij speelt links, de bot rechts. Jullie doen om de beurt een zet en krijgen dezelfde tegels. Wie als eerste de doelscore haalt (1 000, 2 500 of 5 000), wint. Zit iemand vast, dan wint de hoogste score.
- **Tegen een vriend**: je maakt een kamer en deelt de code of de link. Je vriend opent die op een ander toestel in hetzelfde wifi-netwerk (bv. `http://192.168.0.24:8000/kamer/4F7K`). Vraagt Windows om toegang via de firewall, kies dan *privénetwerk*.

## Besturing

Pijltjestoetsen of W, A, S, D. Op een AZERTY-toetsenbord werken Z, Q, S, D vanzelf ook.

## Bestanden

| Bestand | Wat |
|---|---|
| `main.py` | Startpunt: start de website, of het spel in de terminal |
| `game.py` | Spelregels: bord, schuiven, samenvoegen, score, nieuwe tegel, game over |
| `app.py` | Webserver: koppelt de website aan de spelregels en de AI |
| `Algoritme/ai.py` | De AI (Expectimax) met drie moeilijkheden |
| `Web/` | De website: `index.html`, `style.css` en `app.js` |
| `interface_layout/` | Het ontwerp van de schermen |
| `interface/` | Eerste versie van de interface in tkinter (wordt niet gebruikt door `main.py`) |

## Hoe werkt het?

Het project bestaat uit drie delen:

1. **Spelregels (`game.py`)**: het bord is een raster van 4x4. Bij een zet schuiven alle tegels in één richting, en gelijke tegels smelten samen. Elke tegel smelt maar één keer per zet: `[2, 2, 2, 2]` wordt `[4, 4, 0, 0]`. Na een geldige zet verschijnt er op een willekeurig leeg vak een nieuwe tegel: in 90% van de gevallen een 2, anders een 4. Het spel is gedaan als geen enkele zet nog iets verandert.
2. **AI (`Algoritme/ai.py`)**: kiest de zet voor de bot (zie hieronder).
3. **Interface (`Web/`)**: toont de schermen in de browser. Hier kies je de modus, de moeilijkheid en de doelscore.

## Main

Main is de lijm tussen de spelregels, de AI en de interface. `main.py` start alles, `app.py` is een kleine webserver (alleen de standaardbibliotheek van Python). De browser stuurt elke actie naar de server (bv. `POST /api/move`) en krijgt het nieuwe bord terug als JSON. De server:

- start een nieuw spel met de modus, de moeilijkheid en de doelscore die op het startscherm gekozen zijn,
- voert de zet van de speler uit, telt de punten op bij de score en zet een nieuwe tegel op het bord,
- houdt de vorige zetten bij, zodat je in singleplayer een zet ongedaan kan maken,
- laat in de modus "tegen de bot" daarna de AI zijn zet kiezen, met een korte pauze zodat je kan volgen wat hij doet,
- controleert na elke zet of iemand de doelscore haalt of vastloopt,
- beheert bij "tegen een vriend" de kamers: een code maken, meedoen, en om de beurt een zet doen.

## De interface

De interface toont het spel en vangt de invoer van de speler op. `Web/app.js` tekent het juiste scherm (start, singleplayer, tegen de bot, kamer, einde van de ronde) en stuurt elke zet naar de server. De interface beslist zelf niets over het spel.

Het bord wordt opnieuw getekend na elke zet. Elke tegelwaarde heeft een eigen kleur: hoe hoger de waarde, hoe feller de kleur.

## De AI

De AI gebruikt **Expectimax**. In 2048 speel je niet tegen een tegenstander die je wil laten verliezen, maar tegen het toeval. De AI wisselt daarom af tussen twee stappen:

- **zelf kiezen**: welke zet is de beste?
- **toeval**: wat is het verwachte resultaat, gemiddeld over alle plaatsen waar de nieuwe tegel kan verschijnen?

Aan het einde van de zoektocht krijgt elk bord een score. Een bord scoort hoger als het:

- veel lege vakken heeft,
- veel tegels heeft die kunnen samensmelten,
- netjes oploopt naar één hoek (de "hoekstrategie"),
- weinig grote tegels heeft die verspreid over het bord liggen.

### Moeilijkheden

| Niveau | Hoe de bot denkt |
|---|---|
| Easy | Kijkt alleen naar de punten van deze zet en doet vaak (30%) een willekeurige zet. |
| Middel | Kijkt één zet vooruit, rekening houdend met de nieuwe tegel, en maakt af en toe (5%) een fout. |
| Hard | Kijkt twee tot drie zetten vooruit en maakt geen fouten. Als het bord voller wordt, zoekt hij dieper. |

## Testen

```
python game.py
```

Toont een startbord, hoe dat eruitziet na elke zet (met de punten), en of een vol bord zonder zetten als game over gezien wordt.
