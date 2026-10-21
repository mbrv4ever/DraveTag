DraveTag - media-tags bewerken en bulk hernoemen
=================================================

DraveTag bewerkt de tags (informatie) van je muziek en foto's, en kan een hele
map bestanden in een keer netjes hernoemen. Alles lokaal en offline.

STARTEN
- Dubbelklik run.bat. De eerste keer installeert hij eenmalig de benodigde
  onderdelen (PyQt6, mutagen, piexif). Daarna start de app meteen.
- Werkt er iets niet? Draai start-debug.bat (toont fouten) of herstel.bat.

GEBRUIK
- 'Map openen' en kies een map met muziek of foto's.
- Links de lijst; met 'Type' filter je op Muziek of Foto's.
- Selecteer een of meer bestanden (Ctrl/Shift voor meerdere).

TABBLAD TAGS BEWERKEN
- Muziek (mp3, flac, m4a, ogg...): Titel, Artiest, Album, Albumartiest, Jaar,
  Nummer, Genre.
- Foto (jpg/tiff): Beschrijving, Maker, Copyright, Datum (plus de camera).
- Links zie je een voorbeeld: bij een foto de afbeelding, bij muziek/video de
  albumhoes (als die erin zit) plus info (duur, kbps, grootte).
- Pas velden aan en klik 'Opslaan'.
- Meerdere bestanden geselecteerd? Dan worden alleen de INGEVULDE velden op alle
  geselecteerde toegepast (handig om in een keer album of artiest te zetten).

TABBLAD BULK HERNOEMEN
- Kies een manier: Zoek en vervang / Voor-achtervoegsel / Doornummeren /
  Uit tags (muziek, bv. {artist} - {title}).
- Je ziet eerst een VOORBEELD (oud -> nieuw). Pas bij 'Toepassen' worden de
  bestanden echt hernoemd. De extensie blijft behouden; dubbele namen krijgen
  automatisch (2), (3)...

LET OP
- Bewerken en hernoemen wijzigen je echte bestanden. Maak bij twijfel eerst een
  kopie van de map.

EIGEN .EXE MAKEN (optioneel)
- Draai eerst run.bat (voor de .venv), daarna bouw-exe.bat -> dist\DraveTag.exe.

Vragen of een tip? service@dravenlock.nl
Steun de ontwikkeling: https://paypal.me/roger076
