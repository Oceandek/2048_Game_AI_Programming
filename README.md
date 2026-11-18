# 2048 AI

Schoolproject AI Programming (VIVES Brugge, Elektronica-ICT, 2026-2027).

We maken het spel 2048, maar dan speelt een AI het zelf. Voor elke zet kijkt de AI vooruit naar wat er kan gebeuren, inclusief de willekeurige nieuwe tegel, en kiest daarna de beste zet.

## Wie doet wat

<img src="https://github.com/LarsYse.png" width="24" align="center"> **[Lars Ysebaert](https://github.com/LarsYse)**: interface (het spel op het scherm tonen)

<img src="https://github.com/Oceandek.png" width="24" align="center"> **[Ocean Dekeyser](https://github.com/Oceandek)**: main (spelregels, bord en alles aan elkaar koppelen)

<img src="https://github.com/Brent69420809.png" width="24" align="center"> **[Brent Vileyn](https://github.com/Brent69420809)**: algoritme (de AI die de beste zet kiest)

## Gamemodes
 
- **Singleplayer**: je speelt alleen en probeert de 2048-tegel te halen.
- **Tegen de bot**: jij speelt links, de bot rechts. Jullie doen om de beurt een zet. Wie als eerste de doelscore haalt (1 000, 2 500 of 5 000), wint.
- **Tegen een vriend**: je maakt een kamer en deelt de code. Deze modus is nog in ontwikkeling.
## Besturing
 
Je gebruikt de pijltjestoetsen of W, A, S en D.
 
## Hoe werkt het?
 
Het project bestaat uit drie delen:
 
1. **Spelregels (`game.py`)**: het bord is een raster van 4x4. Bij een zet schuiven alle tegels in één richting, en gelijke tegels smelten samen. Na een geldige zet verschijnt er op een willekeurig leeg vak een nieuwe tegel: in 90% van de gevallen een 2, anders een 4. Het spel is gedaan als geen enkele zet nog iets verandert.
2. **AI (`ai.py`)**: kiest de zet voor de bot (zie hieronder).
3. **Interface (`ui_base.py` en `screen_*.py`)**: toont het startscherm en het bord. Hier kies je de modus, de moeilijkheid en de doelscore. `main.py` koppelt de interface aan de spelregels en de AI.
## De interface
 
De interface toont het spel op het scherm en vangt de invoer van de speler op. Ze bestaat uit:
 
- **een basis (`ui_base.py`)**: de kleuren, de lettertypes en kleine tekenhulpjes voor knoppen, kaarten en het bord. Hier wordt ook bijgehouden waar je klikt en welke toets je indrukt.
- **schermen (`screen_*.py`)**: elk scherm staat in een eigen bestand. Op het startscherm kies je de modus, de moeilijkheid van de bot en de doelscore.
Het bord wordt opnieuw getekend na elke zet. Elke tegelwaarde heeft een eigen kleur: hoe hoger de waarde, hoe feller de kleur. De interface beslist zelf niets over het spel. Elke klik of toets wordt doorgegeven aan main.
 
## Main
 
Main is de lijm tussen de spelregels, de AI en de interface. Main:
 
- start een nieuw spel met de modus, de moeilijkheid en de doelscore die op het startscherm gekozen zijn,
- voert de zet van de speler uit, telt de punten op bij de score en zet een nieuwe tegel op het bord,
- laat in de modus "tegen de bot" daarna de AI zijn zet kiezen, met een korte pauze zodat je kan volgen wat hij doet,
- controleert na elke zet of iemand de doelscore haalt of vastloopt,
- geeft het nieuwe bord en de score door aan de interface.
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
| Easy | Kijkt alleen naar de punten van deze zet en doet vaak een willekeurige zet. |
| Middel | Kijkt één zet vooruit, rekening houdend met de nieuwe tegel, en maakt af en toe een fout. |
| Hard | Kijkt twee tot drie zetten vooruit en maakt geen fouten. Als het bord voller wordt, zoekt hij dieper. |
 
## Gebruikt
 
- Python 3
- Tkinter voor de interface (zit standaard in Python). We onderzoeken ook een versie die in de webbrowser draait, maar die is nog in ontwikkeling.
- Geen extra pakketten nodig
## Starten
 
```
python main.py
```
 
## Testen
 
```
python test_game.py
```
 
