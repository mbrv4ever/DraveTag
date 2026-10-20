#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DraveTag - lokaal media-tags bewerken (muziek + foto's) en bulk hernoemen.
Dravenlock-huisstijl. Werkt offline.
"""
import os
import sys
import json

from PyQt6.QtCore import Qt, QTimer, QLocale, QUrl
from PyQt6.QtGui import (QPixmap, QIcon, QDesktopServices, QFont, QColor,
                         QBrush, QPen, QPainter, QPalette, QImage)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QSplitter, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QDialog, QToolButton, QFrame, QStatusBar, QComboBox,
    QLineEdit, QFormLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QStackedWidget, QSpinBox, QPlainTextEdit,
    QTextBrowser, QSlider)

try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    HAS_MEDIA = True
except Exception:
    HAS_MEDIA = False

# media-motoren
import mutagen
from mutagen import File as MutaFile
import piexif

APP_NAME = "DraveTag"
APP_VERSION = "0.5"
DONATE_URL = "https://paypal.me/roger076"
SUPPORT_MAIL = "service@dravenlock.nl"

# ---- Dravenlock-huisstijl ----
BG = "#0e0e11"
PANEL = "#16161b"
PANEL2 = "#1c1c22"
SILVER = "#d4d4d4"
MUTE = "#8a8a94"
ACCENT = "#6fa3d6"
LINE = "#23232b"

AUDIO_EXT = {".mp3", ".flac", ".m4a", ".ogg", ".opus", ".oga", ".wma", ".aac"}
VIDEO_EXT = {".mp4", ".m4v", ".mov", ".mkv", ".avi", ".webm", ".wmv"}
IMAGE_EXT = {".jpg", ".jpeg", ".tif", ".tiff"}
# bestanden waarvan mutagen de tags kan lezen/schrijven (audio + mp4-familie video)
MUTA_EXT = AUDIO_EXT | {".mp4", ".m4v", ".mov"}

AUDIO_KEYS = ["title", "artist", "album", "albumartist", "date",
              "tracknumber", "genre"]
AUDIO_LABELS_NL = {"title": "Titel", "artist": "Artiest", "album": "Album",
                   "albumartist": "Albumartiest", "date": "Jaar",
                   "tracknumber": "Nummer", "genre": "Genre"}

IMG_KEYS = ["desc", "artist", "copyright", "datetime"]
IMG_LABELS_NL = {"desc": "Beschrijving", "artist": "Maker",
                 "copyright": "Copyright",
                 "datetime": "Datum (jjjj:mm:dd uu:mm:ss)"}


# ---------------------------------------------------------------------------
# Pad / config
# ---------------------------------------------------------------------------
def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _config_path():
    return os.path.join(_app_dir(), "dravetag_config.json")


DEFAULT_CONFIG = {"lang": "", "last_dir": "", "font_size": 14}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Taal
# ---------------------------------------------------------------------------
_LANG = "nl"

TRANSLATIONS = {
    "en": {
        "Map openen\u2026": "Open folder\u2026",
        "Bestanden openen\u2026": "Open files\u2026",
        "Mediabestanden": "Media files", "Alle bestanden (*)": "All files (*)",
        "(losse bestanden)": "(loose files)",
        "Vernieuwen": "Refresh",
        "Type:": "Type:", "Alles": "All", "Muziek": "Music",
        "Video": "Video", "Foto's": "Photos",
        "Instellingen\u2026": "Settings\u2026", "Snelgids": "Quick guide",
        "Over": "About", "Sluiten": "Close", "Taal:": "Language:",
        "Automatisch (OS)": "Automatic (OS)", "Nederlands": "Dutch",
        "Engels": "English", "Lettergrootte:": "Font size:",
        "Tags bewerken": "Edit tags", "Bulk hernoemen": "Bulk rename",
        "Opslaan": "Save", "Donatie": "Donate",
        "Afspelen": "Play", "Openen in speler": "Open in player",
        "Afspelen in het venster lukte niet; geopend in het standaardprogramma.":
            "In-window playback failed; opened in the default app.",
        "Geen map gekozen": "No folder chosen",
        "bestanden": "files", "geselecteerd": "selected",
        "Selecteer een bestand om de tags te zien.":
            "Select a file to view its tags.",
        "Selecteer bestanden van \u00e9\u00e9n type (allemaal muziek of allemaal foto's).":
            "Select files of one type (all music or all photos).",
        "Dit bestandstype heeft geen bewerkbare tags.":
            "This file type has no editable tags.",
        "Camera:": "Camera:",
        "Tags opslaan op %d bestand(en)?": "Save tags to %d file(s)?",
        "Bij meerdere bestanden worden alleen ingevulde velden toegepast.":
            "With multiple files, only filled-in fields are applied.",
        "Opgeslagen.": "Saved.", "Kon niet opslaan: ": "Could not save: ",
        "Manier:": "Method:",
        "Zoek en vervang": "Find and replace",
        "Voor-/achtervoegsel": "Prefix/suffix",
        "Doornummeren": "Numbering", "Uit tags (muziek)": "From tags (music)",
        "Zoek:": "Find:", "Vervang door:": "Replace with:",
        "Voorvoegsel:": "Prefix:", "Achtervoegsel:": "Suffix:",
        "Basisnaam:": "Base name:", "Startgetal:": "Start number:",
        "Cijfers:": "Digits:", "Patroon:": "Pattern:",
        "Werkt op:": "Applies to:",
        "geselecteerde bestanden": "selected files",
        "alle bestanden in de lijst": "all files in the list",
        "Oud": "Old", "Nieuw": "New", "Toepassen": "Apply",
        "Naam wijzigen van %d bestand(en)?": "Rename %d file(s)?",
        "%d hernoemd": "%d renamed", "Niets te hernoemen.": "Nothing to rename.",
        "snelgids_titel": "DraveTag - quick guide",
    }
}


def detect_lang(cfg):
    forced = (cfg.get("lang") or "").strip().lower()
    if forced in ("nl", "en"):
        return forced
    try:
        if QLocale.system().name().lower().startswith("nl"):
            return "nl"
        return "en"
    except Exception:
        return "nl"


def t(s, lang=None):
    lg = lang or _LANG
    if lg == "nl":
        return s
    return TRANSLATIONS.get(lg, {}).get(s, s)


def audio_label(k, lang):
    nl = AUDIO_LABELS_NL[k]
    return nl if lang == "nl" else {
        "Titel": "Title", "Artiest": "Artist", "Album": "Album",
        "Albumartiest": "Album artist", "Jaar": "Year", "Nummer": "Track",
        "Genre": "Genre"}.get(nl, nl)


def img_label(k, lang):
    nl = IMG_LABELS_NL[k]
    return nl if lang == "nl" else {
        "Beschrijving": "Description", "Maker": "Artist",
        "Copyright": "Copyright",
        "Datum (jjjj:mm:dd uu:mm:ss)": "Date (yyyy:mm:dd hh:mm:ss)"}.get(nl, nl)


# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------
def make_logo(size=32):
    p = os.path.join(_app_dir(), "logo.png")
    if os.path.exists(p):
        pm = QPixmap(p)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    pt = QPainter(pm)
    pt.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    pt.setBrush(QBrush(QColor(ACCENT)))
    pt.setPen(Qt.PenStyle.NoPen)
    pt.drawRoundedRect(int(s * 0.2), int(s * 0.2), int(s * 0.6), int(s * 0.6),
                       int(s * 0.12), int(s * 0.12))
    pt.end()
    return pm


def app_icon():
    p = os.path.join(_app_dir(), "logo.ico")
    if os.path.exists(p):
        return QIcon(p)
    return QIcon(make_logo(64))


# ---------------------------------------------------------------------------
# Media-helpers
# ---------------------------------------------------------------------------
def kind_of(path):
    e = os.path.splitext(path)[1].lower()
    if e in AUDIO_EXT:
        return "audio"
    if e in VIDEO_EXT:
        return "video"
    if e in IMAGE_EXT:
        return "image"
    return "other"


def tag_group(path):
    """Welke tag-bewerker past: 'muta' (mutagen), 'image' (exif) of 'none'."""
    e = os.path.splitext(path)[1].lower()
    if e in MUTA_EXT:
        return "muta"
    if e in IMAGE_EXT:
        return "image"
    return "none"


def read_audio(path):
    out = {k: "" for k in AUDIO_KEYS}
    try:
        f = MutaFile(path, easy=True)
        if f is None:
            return out
        for k in AUDIO_KEYS:
            try:
                v = f[k]
                if v:
                    out[k] = v[0] if isinstance(v, (list, tuple)) else str(v)
            except Exception:
                pass
    except Exception:
        pass
    return out


def write_audio(path, fields, only_nonempty=False):
    f = MutaFile(path, easy=True)
    if f is None:
        raise ValueError("niet-ondersteund audiobestand")
    if f.tags is None:
        f.add_tags()
    for k in AUDIO_KEYS:
        if k not in fields:
            continue
        val = (fields[k] or "").strip()
        if only_nonempty and not val:
            continue
        if not val:
            try:
                if k in f:
                    del f[k]
            except Exception:
                pass
        else:
            f[k] = [val]
    f.save()


_EXIF_MAP = {
    "desc": ("0th", piexif.ImageIFD.ImageDescription),
    "artist": ("0th", piexif.ImageIFD.Artist),
    "copyright": ("0th", piexif.ImageIFD.Copyright),
    "datetime": ("Exif", piexif.ExifIFD.DateTimeOriginal),
}


def _dec(v):
    if isinstance(v, bytes):
        return v.decode("utf-8", "ignore").rstrip("\x00")
    return str(v) if v is not None else ""


def read_image(path):
    out = {k: "" for k in IMG_KEYS}
    out["_camera"] = ""
    try:
        ex = piexif.load(path)
        for k, (ifd, tag) in _EXIF_MAP.items():
            v = ex.get(ifd, {}).get(tag)
            if v is not None:
                out[k] = _dec(v)
        make = _dec(ex.get("0th", {}).get(piexif.ImageIFD.Make))
        model = _dec(ex.get("0th", {}).get(piexif.ImageIFD.Model))
        out["_camera"] = (make + " " + model).strip()
    except Exception:
        pass
    return out


def write_image(path, fields, only_nonempty=False):
    try:
        ex = piexif.load(path)
    except Exception:
        ex = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    for k, (ifd, tag) in _EXIF_MAP.items():
        if k not in fields:
            continue
        val = (fields[k] or "").strip()
        if only_nonempty and not val:
            continue
        ex.setdefault(ifd, {})
        if not val:
            if tag in ex[ifd]:
                del ex[ifd][tag]
        else:
            ex[ifd][tag] = val.encode("utf-8")
    try:
        data = piexif.dump(ex)
    except Exception:
        # sommige miniatuur/1st-velden kunnen dump breken -> laten vallen
        ex["1st"] = {}
        ex["thumbnail"] = None
        data = piexif.dump(ex)
    piexif.insert(data, path)


def sanitize_stem(name, fallback="bestand"):
    name = (name or "").strip()
    for ch in '<>:"/\\|?*\n\r\t':
        name = name.replace(ch, " ")
    name = " ".join(name.split()).strip(" .")
    return name[:120] or fallback


def _human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return ("%.0f %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024.0
    return "%d B" % n


def _mmss(sec):
    sec = int(round(sec))
    return "%d:%02d" % (sec // 60, sec % 60)


def cover_bytes(path):
    """Ingebouwde albumhoes/cover uit een audio/video-bestand (of None)."""
    try:
        f = MutaFile(path)
        if f is None:
            return None
        pics = getattr(f, "pictures", None)   # FLAC
        if pics:
            return pics[0].data
        tags = getattr(f, "tags", None)
        if not tags:
            return None
        try:
            for k in tags.keys():             # MP3 APIC
                if str(k).startswith("APIC"):
                    return tags[k].data
        except Exception:
            pass
        if "covr" in tags:                    # MP4/M4A covr
            c = tags["covr"]
            if c:
                return bytes(c[0])
    except Exception:
        return None
    return None


def media_info(path):
    k = kind_of(path)
    parts = []
    try:
        if k in ("audio", "video"):
            f = MutaFile(path)
            info = getattr(f, "info", None) if f is not None else None
            if info is not None:
                if getattr(info, "length", 0):
                    parts.append(_mmss(info.length))
                if getattr(info, "bitrate", 0):
                    parts.append("%d kbps" % (info.bitrate // 1000))
        elif k == "image":
            img = QImage(path)
            if not img.isNull():
                parts.append("%d x %d" % (img.width(), img.height()))
    except Exception:
        pass
    try:
        parts.append(_human_size(os.path.getsize(path)))
    except Exception:
        pass
    return "  \u00b7  ".join(parts)


def video_thumbnail(path, frac=0.25):
    """Een beeld uit de video (QImage) of None. OpenCV is optioneel."""
    try:
        import cv2
    except Exception:
        return None
    cap = None
    try:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return None
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if n > 1:
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, min(n - 1, int(n * frac))))
        ok, frame = cap.read()
        if not ok or frame is None:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
        if not ok or frame is None:
            return None
        import numpy as np
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.ascontiguousarray(frame)
        h, w = frame.shape[:2]
        return QImage(frame.data, w, h, 3 * w,
                      QImage.Format.Format_RGB888).copy()
    except Exception:
        return None
    finally:
        try:
            if cap is not None:
                cap.release()
        except Exception:
            pass


def placeholder_pixmap(kind, size=240):
    pm = QPixmap(size, size)
    pm.fill(QColor(PANEL2))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(MUTE), 2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    c = size / 2
    if kind == "audio":
        # nootje
        p.setBrush(QBrush(QColor(ACCENT)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(c - 46), int(c + 6), 34, 26)
        p.drawEllipse(int(c + 20), int(c - 8), 34, 26)
        p.setPen(QPen(QColor(ACCENT), 7))
        p.drawLine(int(c - 14), int(c + 19), int(c - 14), int(c - 44))
        p.drawLine(int(c + 52), int(c + 5), int(c + 52), int(c - 30))
        p.drawLine(int(c - 14), int(c - 44), int(c + 52), int(c - 30))
    elif kind == "video":
        p.setBrush(QBrush(QColor(ACCENT)))
        p.setPen(Qt.PenStyle.NoPen)
        tri = [(int(c - 28), int(c - 36)), (int(c - 28), int(c + 36)),
               (int(c + 40), int(c))]
        from PyQt6.QtGui import QPolygon
        from PyQt6.QtCore import QPoint
        p.drawPolygon(QPolygon([QPoint(x, y) for x, y in tri]))
    else:
        p.setPen(QPen(QColor(MUTE), 2))
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "?")
    p.end()
    return pm


# ---------------------------------------------------------------------------
# Snelgids
# ---------------------------------------------------------------------------
GUIDE_NL = """DraveTag - Snelgids

DraveTag bewerkt de tags (informatie) van je muziek en foto's, en kan een
hele map bestanden in een keer netjes hernoemen. Alles lokaal en offline.

Aan de slag
- Klik op 'Map openen' voor een hele map, of 'Bestanden openen' om losse
  bestanden te kiezen (ook uit verschillende mappen).
- Links verschijnt de lijst. Met 'Type' filter je op Muziek, Video of Foto's.
- Selecteer een of meer bestanden (Ctrl/Shift om meerdere te kiezen).

Tabblad 'Tags bewerken'
- Bij een muziekbestand: Titel, Artiest, Album, Jaar, Nummer, Genre...
- Bij een foto: Beschrijving, Maker, Copyright, Datum (en de camera).
- Links zie je een voorbeeld: bij een foto de afbeelding, bij video een beeld uit
  de film, bij muziek de albumhoes (als die erin zit), plus info (duur, kbps,
  grootte). Met 'Afspelen' speelt video of muziek IN het venster af (met
  play/pauze, een tijdbalk en stop) - geen aparte speler nodig. Foto's open je
  met 'Openen' in je standaardprogramma.
- Pas de velden aan en klik 'Opslaan'.
- Heb je meerdere bestanden geselecteerd? Dan worden alleen de velden die je
  invult op alle geselecteerde bestanden toegepast (handig om bv. in een keer
  het album of de artiest te zetten). Lege velden blijven dan ongemoeid.

Tabblad 'Bulk hernoemen'
- Kies een manier:
  - Zoek en vervang: vervang tekst in de bestandsnamen.
  - Voor-/achtervoegsel: zet tekst voor of achter de naam.
  - Doornummeren: bv. 'Vakantie 001', 'Vakantie 002'...
  - Uit tags (muziek): bouw de naam uit de tags, bv. {artist} - {title}.
- Je ziet altijd eerst een VOORBEELD (oud -> nieuw). Pas als je op 'Toepassen'
  klikt, worden de bestanden echt hernoemd. De extensie blijft behouden.

Let op
- Bewerken en hernoemen wijzigen je echte bestanden. Maak bij twijfel eerst een
  kopie van de map.

Vragen of een tip? service@dravenlock.nl
"""

GUIDE_EN = """DraveTag - Quick guide

DraveTag edits the tags (information) of your music and photos, and can rename
a whole folder of files at once. Everything local and offline.

Getting started
- Click 'Open folder' for a whole folder, or 'Open files' to pick loose files
  (even from different folders).
- The list appears on the left. Use 'Type' to filter Music, Video or Photos.
- Select one or more files (Ctrl/Shift to pick several).

'Edit tags' tab
- Music files (mp3, flac, m4a, ogg...) and mp4 video: Title, Artist, Album,
  Year, Track, Genre. (mkv/avi can be listed and renamed, but not tagged.)
- For a photo: Description, Artist, Copyright, Date (and the camera).
- On the left you see a preview: for a photo the image, for video a frame from
  the film, for music the cover art (if present), plus info (duration, kbps,
  size). 'Play' plays video or music INSIDE the window (with play/pause, a
  seek bar and stop) - no separate player needed. Photos open with 'Open' in
  your default app.
- Change the fields and click 'Save'.
- Selected several files? Then only the fields you fill in are applied to all
  selected files (handy to set e.g. the album or artist at once). Empty fields
  are left untouched.

'Bulk rename' tab
- Choose a method:
  - Find and replace: replace text in the file names.
  - Prefix/suffix: put text before or after the name.
  - Numbering: e.g. 'Holiday 001', 'Holiday 002'...
  - From tags (music): build the name from the tags, e.g. {artist} - {title}.
- You always see a PREVIEW first (old -> new). Only when you click 'Apply' are
  the files actually renamed. The extension is kept.

Note
- Editing and renaming change your real files. When in doubt, copy the folder
  first.

Questions or feedback? service@dravenlock.nl
"""


class GuideDialog(QDialog):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.setWindowTitle(t("snelgids_titel", lang))
        self.resize(620, 620)
        lay = QVBoxLayout(self)
        box = QTextBrowser()
        box.setObjectName("guide")
        box.setOpenExternalLinks(True)
        box.setPlainText(GUIDE_NL if lang == "nl" else GUIDE_EN)
        lay.addWidget(box)
        row = QHBoxLayout()
        donate = QPushButton("\u2665 " + t("Donatie", lang))
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        row.addWidget(donate)
        row.addStretch(1)
        close = QPushButton(t("Sluiten", lang))
        close.clicked.connect(self.accept)
        row.addWidget(close)
        lay.addLayout(row)


# ---------------------------------------------------------------------------
# Instellingen
# ---------------------------------------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent, cfg, lang):
        super().__init__(parent)
        self.cfg = dict(cfg)
        self.lang = lang
        self.setWindowTitle(t("Instellingen\u2026", lang))
        self.resize(380, 200)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(t("Taal:", lang)))
        self.langbox = QComboBox()
        self.langbox.addItem(t("Automatisch (OS)", lang), "")
        self.langbox.addItem(t("Nederlands", lang), "nl")
        self.langbox.addItem(t("Engels", lang), "en")
        self.langbox.setCurrentIndex({"": 0, "nl": 1, "en": 2}
                                     .get(cfg.get("lang", ""), 0))
        lay.addWidget(self.langbox)
        row = QHBoxLayout()
        row.addWidget(QLabel(t("Lettergrootte:", lang)))
        self.fs = QSpinBox()
        self.fs.setRange(10, 28)
        self.fs.setValue(int(cfg.get("font_size", 14)))
        row.addWidget(self.fs)
        row.addStretch(1)
        lay.addLayout(row)
        hint = QLabel(t("Sommige instellingen gaan pas in na herstarten.", lang)
                      if lang == "nl" else "Some settings apply after a restart.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch(1)
        rr = QHBoxLayout()
        rr.addStretch(1)
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        rr.addWidget(ok)
        lay.addLayout(rr)

    def result_cfg(self):
        self.cfg["lang"] = self.langbox.currentData()
        self.cfg["font_size"] = self.fs.value()
        return self.cfg


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class DraveTag(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.lang = _LANG
        self.font_size = int(cfg.get("font_size", 14))
        self.source_folder = ""   # map indien via 'Map openen', anders ""
        self.entries = []         # volledige paden (map-scan of losse keuze)
        self.tag_widgets = {}      # huidige tag-velden (key -> QLineEdit)
        self.tag_mode = None       # 'muta' / 'image' / None
        self.cam_label = None

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.resize(1140, 770)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header())
        outer.addWidget(self._toolbar())

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._file_panel())
        split.addWidget(self._tabs())
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes([360, 780])
        outer.addWidget(split, 1)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self.count_lbl = QLabel("")
        self.count_lbl.setObjectName("muted")
        sb.addWidget(self.count_lbl)
        sb.addPermanentWidget(QLabel("v" + APP_VERSION))
        donate = QToolButton()
        donate.setText("\u2665 " + t("Donatie", self.lang))
        donate.setObjectName("donate")
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        sb.addPermanentWidget(donate)

        self._apply_fonts()
        last = cfg.get("last_dir", "")
        if last and os.path.isdir(last):
            self.load_folder(last)
        else:
            self._refresh_tags()

    # ---- UI ----
    def _header(self):
        w = QWidget()
        w.setObjectName("header")
        w.setFixedHeight(56)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(14, 8, 14, 8)
        logo = QLabel()
        logo.setPixmap(make_logo(32))
        lay.addWidget(logo)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        lay.addWidget(title)
        ver = QLabel("v" + APP_VERSION)
        ver.setObjectName("ver")
        lay.addWidget(ver)
        lay.addStretch(1)
        for label, slot in [(t("Instellingen\u2026", self.lang), self._settings),
                            (t("Snelgids", self.lang), self._guide),
                            (t("Over", self.lang), self._about)]:
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, s=slot: s())
            lay.addWidget(b)
        return w

    def _toolbar(self):
        w = QWidget()
        w.setObjectName("toolbar")
        w.setFixedHeight(48)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(8)
        b_open = QPushButton(t("Map openen\u2026", self.lang))
        b_open.setObjectName("primary")
        b_open.clicked.connect(self.open_folder)
        lay.addWidget(b_open)
        b_files = QPushButton(t("Bestanden openen\u2026", self.lang))
        b_files.clicked.connect(self.open_files)
        lay.addWidget(b_files)
        b_ref = QPushButton(t("Vernieuwen", self.lang))
        b_ref.clicked.connect(self.reload_files)
        lay.addWidget(b_ref)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setObjectName("sep")
        lay.addWidget(sep)
        lay.addWidget(QLabel(t("Type:", self.lang)))
        self.type_box = QComboBox()
        self.type_box.addItem(t("Alles", self.lang), "all")
        self.type_box.addItem(t("Muziek", self.lang), "audio")
        self.type_box.addItem(t("Video", self.lang), "video")
        self.type_box.addItem(t("Foto's", self.lang), "image")
        self.type_box.currentIndexChanged.connect(self._refresh_display)
        lay.addWidget(self.type_box)
        self.folder_lbl = QLabel(t("Geen map gekozen", self.lang))
        self.folder_lbl.setObjectName("muted")
        lay.addWidget(self.folder_lbl, 1)
        return w

    def _file_panel(self):
        w = QWidget()
        w.setObjectName("sidebar")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 8, 10)
        lay.setSpacing(8)
        self.list = QListWidget()
        self.list.setObjectName("filelist")
        self.list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        lp = self.list.palette()
        for grp in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
            lp.setColor(grp, QPalette.ColorRole.Highlight, QColor(ACCENT))
            lp.setColor(grp, QPalette.ColorRole.HighlightedText, QColor("#08131f"))
        self.list.setPalette(lp)
        self.list.itemSelectionChanged.connect(self._on_sel_changed)
        lay.addWidget(self.list, 1)
        row = QHBoxLayout()
        b_all = QPushButton(t("Alles", self.lang))
        b_all.clicked.connect(self.list.selectAll)
        row.addWidget(b_all)
        b_none = QPushButton("\u2014")
        b_none.clicked.connect(self.list.clearSelection)
        row.addWidget(b_none)
        row.addStretch(1)
        lay.addLayout(row)
        return w

    def _tabs(self):
        self.tabs = QTabWidget()
        self.tabs.addTab(self._tags_tab(), t("Tags bewerken", self.lang))
        self.tabs.addTab(self._rename_tab(), t("Bulk hernoemen", self.lang))
        self.tabs.currentChanged.connect(self._on_tab)
        return self.tabs

    # ---- Tags-tab ----
    def _tags_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(16)
        # voorbeeld (links)
        left = QVBoxLayout()
        left.setSpacing(6)
        # stack: miniatuur (label) of video-widget
        self.preview_stack = QStackedWidget()
        self.preview_stack.setFixedSize(240, 240)
        self.preview_img = QLabel()
        self.preview_img.setObjectName("preview")
        self.preview_img.setFixedSize(240, 240)
        self.preview_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_stack.addWidget(self.preview_img)        # index 0
        self.player = None
        if HAS_MEDIA:
            self.video_widget = QVideoWidget()
            self.video_widget.setFixedSize(240, 240)
            self.preview_stack.addWidget(self.video_widget)   # index 1
            self.player = QMediaPlayer(self)
            self.audio_out = QAudioOutput(self)
            self.player.setAudioOutput(self.audio_out)
            self.player.setVideoOutput(self.video_widget)
            self.player.positionChanged.connect(self._on_pos)
            self.player.durationChanged.connect(self._on_dur)
            self.player.playbackStateChanged.connect(self._on_pbstate)
            self.player.errorOccurred.connect(self._on_media_error)
        left.addWidget(self.preview_stack)
        self.preview_info = QLabel("")
        self.preview_info.setObjectName("muted")
        self.preview_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_info.setFixedWidth(240)
        self.preview_info.setWordWrap(True)
        left.addWidget(self.preview_info)
        # 'Afspelen/Openen'-knop (zichtbaar als er niet afgespeeld wordt)
        self.b_open_file = QPushButton(t("Openen", self.lang))
        self.b_open_file.setFixedWidth(240)
        self.b_open_file.clicked.connect(self._play_selected)
        self.b_open_file.setEnabled(False)
        left.addWidget(self.b_open_file)
        # afspeel-besturing (verborgen tot afspelen)
        self.play_ctrl = QWidget()
        self.play_ctrl.setFixedWidth(240)
        pc = QHBoxLayout(self.play_ctrl)
        pc.setContentsMargins(0, 0, 0, 0)
        pc.setSpacing(6)
        self.b_pp = QToolButton()
        self.b_pp.setObjectName("ctrl")
        self.b_pp.setText("\u23f8")
        self.b_pp.clicked.connect(self._toggle_play)
        pc.addWidget(self.b_pp)
        self.pos_slider = QSlider(Qt.Orientation.Horizontal)
        self.pos_slider.setRange(0, 0)
        self.pos_slider.sliderMoved.connect(self._seek)
        pc.addWidget(self.pos_slider, 1)
        self.b_stop = QToolButton()
        self.b_stop.setObjectName("ctrl")
        self.b_stop.setText("\u23f9")
        self.b_stop.clicked.connect(self._stop_play)
        pc.addWidget(self.b_stop)
        self.play_ctrl.setVisible(False)
        left.addWidget(self.play_ctrl)
        left.addStretch(1)
        top.addLayout(left)
        # velden (rechts)
        right = QVBoxLayout()
        right.setSpacing(10)
        self.tag_info = QLabel(t("Selecteer een bestand om de tags te zien.",
                                 self.lang))
        self.tag_info.setObjectName("muted")
        self.tag_info.setWordWrap(True)
        right.addWidget(self.tag_info)
        self.form_host = QWidget()
        self.form_layout = QFormLayout(self.form_host)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.form_layout.setHorizontalSpacing(12)
        self.form_layout.setVerticalSpacing(10)
        right.addWidget(self.form_host)
        right.addStretch(1)
        top.addLayout(right, 1)
        lay.addLayout(top, 1)

        self.b_save_tags = QPushButton(t("Opslaan", self.lang))
        self.b_save_tags.setObjectName("primary")
        self.b_save_tags.clicked.connect(self._save_tags)
        self.b_save_tags.setEnabled(False)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.b_save_tags)
        lay.addLayout(row)
        self._set_preview(None)
        return w

    def _set_preview(self, path):
        self._reset_player()
        if not path:
            self.preview_img.setPixmap(placeholder_pixmap("other"))
            self.preview_info.setText("")
            self.b_open_file.setEnabled(False)
            self.b_open_file.setText(t("Openen", self.lang))
            return
        k = kind_of(path)
        pm = None
        if k == "image":
            img = QPixmap(path)
            if not img.isNull():
                pm = img
        else:
            data = cover_bytes(path)
            if data:
                img = QPixmap()
                if img.loadFromData(data):
                    pm = img
            if pm is None and k == "video":
                qi = video_thumbnail(path)
                if qi is not None and not qi.isNull():
                    pm = QPixmap.fromImage(qi)
        if pm is not None:
            self.preview_img.setPixmap(pm.scaled(
                238, 238, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            self.preview_img.setPixmap(placeholder_pixmap(k))
        self.preview_info.setText(media_info(path))
        self.b_open_file.setEnabled(True)
        if k in ("audio", "video") and HAS_MEDIA:
            self.b_open_file.setText(t("Afspelen", self.lang))
        else:
            self.b_open_file.setText(t("Openen", self.lang))

    # ---- ingebouwde speler ----
    def _reset_player(self):
        if HAS_MEDIA and self.player is not None:
            self.player.stop()
        if hasattr(self, "preview_stack"):
            self.preview_stack.setCurrentIndex(0)
        if hasattr(self, "play_ctrl"):
            self.play_ctrl.setVisible(False)
        if hasattr(self, "b_open_file"):
            self.b_open_file.setVisible(True)

    def _play_selected(self):
        sel = self._selected_paths()
        if not sel:
            return
        p = sel[0]
        k = kind_of(p)
        if not HAS_MEDIA or self.player is None or k == "image":
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))
            return
        self._playing_path = p
        self.player.setSource(QUrl.fromLocalFile(p))
        self.preview_stack.setCurrentIndex(1 if k == "video" else 0)
        self.b_open_file.setVisible(False)
        self.play_ctrl.setVisible(True)
        self.player.play()

    def _toggle_play(self):
        if not self.player:
            return
        if (self.player.playbackState()
                == QMediaPlayer.PlaybackState.PlayingState):
            self.player.pause()
        else:
            self.player.play()

    def _stop_play(self):
        if self.player:
            self.player.stop()
        self._reset_player()

    def _seek(self, val):
        if self.player:
            self.player.setPosition(val)

    def _on_pos(self, pos):
        if not self.pos_slider.isSliderDown():
            self.pos_slider.blockSignals(True)
            self.pos_slider.setValue(pos)
            self.pos_slider.blockSignals(False)

    def _on_dur(self, dur):
        self.pos_slider.setRange(0, dur)

    def _on_pbstate(self, state):
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.b_pp.setText("\u23f8" if playing else "\u25b6")
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.preview_stack.setCurrentIndex(0)
            self.play_ctrl.setVisible(False)
            self.b_open_file.setVisible(True)

    def _on_media_error(self, *args):
        p = getattr(self, "_playing_path", None)
        self._stop_play()
        if p:
            self.statusBar().showMessage(
                t("Afspelen in het venster lukte niet; geopend in het "
                  "standaardprogramma.", self.lang), 5000)
            QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def _clear_form(self):
        while self.form_layout.rowCount():
            self.form_layout.removeRow(0)
        self.tag_widgets = {}
        self.cam_label = None

    def _refresh_tags(self):
        self._clear_form()
        self.tag_mode = None
        sel = self._selected_paths()
        if not sel:
            self.tag_info.setText(
                t("Selecteer een bestand om de tags te zien.", self.lang))
            self.b_save_tags.setEnabled(False)
            self._set_preview(None)
            return
        self._set_preview(sel[0])
        groups = set(tag_group(p) for p in sel)
        if groups == {"muta"}:
            self.tag_mode = "muta"
            self._build_audio_form(sel)
        elif groups == {"image"}:
            self.tag_mode = "image"
            self._build_image_form(sel)
        elif groups <= {"none"}:
            self.tag_info.setText(
                t("Dit bestandstype heeft geen bewerkbare tags.", self.lang))
            self.b_save_tags.setEnabled(False)
        else:
            self.tag_info.setText(t(
                "Selecteer bestanden van \u00e9\u00e9n type "
                "(allemaal muziek of allemaal foto's).", self.lang))
            self.b_save_tags.setEnabled(False)

    def _build_audio_form(self, sel):
        single = len(sel) == 1
        vals = read_audio(sel[0]) if single else {k: "" for k in AUDIO_KEYS}
        if single:
            self.tag_info.setText(os.path.basename(sel[0]))
        else:
            self.tag_info.setText("%d %s \u00b7 %s" % (
                len(sel), t("geselecteerd", self.lang),
                t("Bij meerdere bestanden worden alleen ingevulde velden "
                  "toegepast.", self.lang)))
        for k in AUDIO_KEYS:
            le = QLineEdit(vals.get(k, ""))
            self.tag_widgets[k] = le
            self.form_layout.addRow(audio_label(k, self.lang) + ":", le)
        self.b_save_tags.setEnabled(True)

    def _build_image_form(self, sel):
        single = len(sel) == 1
        vals = read_image(sel[0]) if single else {k: "" for k in IMG_KEYS}
        if single:
            self.tag_info.setText(os.path.basename(sel[0]))
        else:
            self.tag_info.setText("%d %s \u00b7 %s" % (
                len(sel), t("geselecteerd", self.lang),
                t("Bij meerdere bestanden worden alleen ingevulde velden "
                  "toegepast.", self.lang)))
        for k in IMG_KEYS:
            le = QLineEdit(vals.get(k, ""))
            self.tag_widgets[k] = le
            self.form_layout.addRow(img_label(k, self.lang) + ":", le)
        if single and vals.get("_camera"):
            cam = QLabel(vals["_camera"])
            cam.setObjectName("muted")
            self.form_layout.addRow(t("Camera:", self.lang), cam)
        self.b_save_tags.setEnabled(True)

    def _save_tags(self):
        sel = self._selected_paths()
        sel = [p for p in sel if tag_group(p) == self.tag_mode]
        if not sel or not self.tag_mode:
            return
        fields = {k: w.text() for k, w in self.tag_widgets.items()}
        batch = len(sel) > 1
        if batch:
            r = QMessageBox.question(
                self, APP_NAME,
                t("Tags opslaan op %d bestand(en)?", self.lang) % len(sel))
            if r != QMessageBox.StandardButton.Yes:
                return
        ok, fail = 0, []
        for p in sel:
            try:
                if self.tag_mode == "muta":
                    write_audio(p, fields, only_nonempty=batch)
                else:
                    write_image(p, fields, only_nonempty=batch)
                ok += 1
            except Exception as e:
                fail.append("%s: %s" % (os.path.basename(p), e))
        if fail:
            QMessageBox.warning(self, APP_NAME,
                                t("Kon niet opslaan: ", self.lang)
                                + "\n".join(fail[:6]))
        else:
            self.statusBar().showMessage(t("Opgeslagen.", self.lang), 3000)
        self._refresh_tags()

    # ---- Hernoemen-tab ----
    def _rename_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        top = QHBoxLayout()
        top.addWidget(QLabel(t("Manier:", self.lang)))
        self.mode_box = QComboBox()
        for label, key in [(t("Zoek en vervang", self.lang), "replace"),
                           (t("Voor-/achtervoegsel", self.lang), "affix"),
                           (t("Doornummeren", self.lang), "number"),
                           (t("Uit tags (muziek)", self.lang), "fromtags")]:
            self.mode_box.addItem(label, key)
        self.mode_box.currentIndexChanged.connect(self._mode_changed)
        top.addWidget(self.mode_box)
        top.addStretch(1)
        lay.addLayout(top)

        self.mode_stack = QStackedWidget()
        self.mode_stack.addWidget(self._page_replace())
        self.mode_stack.addWidget(self._page_affix())
        self.mode_stack.addWidget(self._page_number())
        self.mode_stack.addWidget(self._page_fromtags())
        lay.addWidget(self.mode_stack)

        self.scope_lbl = QLabel("")
        self.scope_lbl.setObjectName("muted")
        lay.addWidget(self.scope_lbl)

        self.preview = QTableWidget(0, 2)
        self.preview.setHorizontalHeaderLabels([t("Oud", self.lang),
                                                t("Nieuw", self.lang)])
        self.preview.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.preview.verticalHeader().setVisible(False)
        self.preview.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preview.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection)
        lay.addWidget(self.preview, 1)

        row = QHBoxLayout()
        row.addStretch(1)
        self.b_apply = QPushButton(t("Toepassen", self.lang))
        self.b_apply.setObjectName("primary")
        self.b_apply.clicked.connect(self._apply_rename)
        row.addWidget(self.b_apply)
        lay.addLayout(row)
        return w

    def _form_page(self, rows):
        page = QWidget()
        fl = QFormLayout(page)
        fl.setHorizontalSpacing(12)
        fl.setVerticalSpacing(10)
        for label, widget in rows:
            fl.addRow(label, widget)
        return page

    def _page_replace(self):
        self.r_find = QLineEdit()
        self.r_repl = QLineEdit()
        for le in (self.r_find, self.r_repl):
            le.textChanged.connect(self._update_preview)
        return self._form_page([(t("Zoek:", self.lang), self.r_find),
                                (t("Vervang door:", self.lang), self.r_repl)])

    def _page_affix(self):
        self.a_pre = QLineEdit()
        self.a_suf = QLineEdit()
        for le in (self.a_pre, self.a_suf):
            le.textChanged.connect(self._update_preview)
        return self._form_page([(t("Voorvoegsel:", self.lang), self.a_pre),
                                (t("Achtervoegsel:", self.lang), self.a_suf)])

    def _page_number(self):
        self.n_base = QLineEdit()
        self.n_base.setPlaceholderText("Vakantie ")
        self.n_start = QSpinBox()
        self.n_start.setRange(0, 999999)
        self.n_start.setValue(1)
        self.n_pad = QSpinBox()
        self.n_pad.setRange(1, 6)
        self.n_pad.setValue(3)
        self.n_base.textChanged.connect(self._update_preview)
        self.n_start.valueChanged.connect(self._update_preview)
        self.n_pad.valueChanged.connect(self._update_preview)
        return self._form_page([(t("Basisnaam:", self.lang), self.n_base),
                                (t("Startgetal:", self.lang), self.n_start),
                                (t("Cijfers:", self.lang), self.n_pad)])

    def _page_fromtags(self):
        self.ft_pat = QLineEdit("{artist} - {title}")
        self.ft_pat.textChanged.connect(self._update_preview)
        hint = QLabel("{artist} {title} {album} {track} {year}")
        hint.setObjectName("muted")
        page = QWidget()
        fl = QFormLayout(page)
        fl.addRow(t("Patroon:", self.lang), self.ft_pat)
        fl.addRow("", hint)
        return page

    def _mode_changed(self):
        self.mode_stack.setCurrentIndex(self.mode_box.currentIndex())
        self._update_preview()

    def _rename_targets(self):
        sel = self._selected_paths()
        if sel:
            files = sel
            self.scope_lbl.setText("%s %d %s" % (
                t("Werkt op:", self.lang), len(files),
                t("geselecteerde bestanden", self.lang)))
        else:
            files = self._all_paths()
            self.scope_lbl.setText("%s %s" % (
                t("Werkt op:", self.lang),
                t("alle bestanden in de lijst", self.lang)))
        return sorted(files, key=lambda p: os.path.basename(p).lower())

    def _compute_new_stem(self, path, idx, tags_cache):
        stem = os.path.splitext(os.path.basename(path))[0]
        mode = self.mode_box.currentData()
        if mode == "replace":
            find = self.r_find.text()
            return stem.replace(find, self.r_repl.text()) if find else stem
        if mode == "affix":
            return self.a_pre.text() + stem + self.a_suf.text()
        if mode == "number":
            base = self.n_base.text()
            return "%s%0*d" % (base, self.n_pad.value(),
                               self.n_start.value() + idx)
        if mode == "fromtags":
            if path not in tags_cache:
                tags_cache[path] = (read_audio(path)
                                    if tag_group(path) == "muta" else {})
            tg = tags_cache[path]
            pat = self.ft_pat.text()
            track = (tg.get("tracknumber", "") or "").split("/")[0]
            s = (pat.replace("{artist}", tg.get("artist", "") or "")
                    .replace("{title}", tg.get("title", "") or "")
                    .replace("{album}", tg.get("album", "") or "")
                    .replace("{year}", (tg.get("date", "") or "")[:4])
                    .replace("{track}", track))
            return s.strip() or stem
        return stem

    def _plan(self):
        """Lijst (oud_pad, nieuw_volledig_pad) met unieke namen, per map."""
        files = self._rename_targets()
        tags_cache = {}
        used = {}      # map -> set(bestaande/gebruikte namen, lowercase)
        moving = {}    # map -> set(normcase basisnamen die meebewegen)
        for p in files:
            folder = os.path.dirname(p)
            moving.setdefault(folder, set()).add(
                os.path.normcase(os.path.basename(p)))
        for folder in moving:
            used[folder] = set()
            try:
                for f in os.listdir(folder):
                    if os.path.normcase(f) not in moving[folder]:
                        used[folder].add(f.lower())
            except Exception:
                pass
        plan = []
        for idx, p in enumerate(files):
            folder = os.path.dirname(p)
            ext = os.path.splitext(p)[1]
            stem = sanitize_stem(self._compute_new_stem(p, idx, tags_cache),
                                 os.path.splitext(os.path.basename(p))[0])
            newname = stem + ext
            seen = used.setdefault(folder, set())
            if newname.lower() in seen:
                n = 2
                while ("%s (%d)%s" % (stem, n, ext)).lower() in seen:
                    n += 1
                newname = "%s (%d)%s" % (stem, n, ext)
            seen.add(newname.lower())
            plan.append((p, os.path.join(folder, newname)))
        return plan

    def _update_preview(self):
        if not self.entries:
            self.preview.setRowCount(0)
            self.scope_lbl.setText("")
            return
        plan = self._plan()
        self.preview.setRowCount(len(plan))
        changed = 0
        for r, (p, newfull) in enumerate(plan):
            old = os.path.basename(p)
            new = os.path.basename(newfull)
            self.preview.setItem(r, 0, QTableWidgetItem(old))
            it = QTableWidgetItem(new)
            if new != old:
                it.setForeground(QBrush(QColor(ACCENT)))
                changed += 1
            self.preview.setItem(r, 1, it)
        self.b_apply.setEnabled(changed > 0)

    def _apply_rename(self):
        plan = [(p, nf) for p, nf in self._plan()
                if os.path.normcase(nf) != os.path.normcase(p)]
        if not plan:
            self.statusBar().showMessage(t("Niets te hernoemen.", self.lang), 3000)
            return
        r = QMessageBox.question(
            self, APP_NAME,
            t("Naam wijzigen van %d bestand(en)?", self.lang) % len(plan))
        if r != QMessageBox.StandardButton.Yes:
            return
        # twee fasen: eerst naar tijdelijke namen (in dezelfde map), dan eindnaam
        temps = []
        done = 0
        renamed = {}
        try:
            for i, (p, nf) in enumerate(plan):
                tmp = os.path.join(os.path.dirname(p), ".dtag_tmp_%d" % i)
                os.replace(p, tmp)
                temps.append((tmp, nf, p))
            for tmp, nf, oldp in temps:
                os.replace(tmp, nf)
                renamed[oldp] = nf
                done += 1
        except Exception as e:
            QMessageBox.warning(self, APP_NAME, str(e))
        # losse-bestandenlijst meeverhuizen
        if not self.source_folder and renamed:
            self.entries = [renamed.get(p, p) for p in self.entries]
        self.statusBar().showMessage(
            t("%d hernoemd", self.lang) % done, 4000)
        self.reload_files()

    # ---- map / losse bestanden / lijst ----
    def open_folder(self):
        d = QFileDialog.getExistingDirectory(
            self, t("Map openen\u2026", self.lang),
            self.source_folder or self.cfg.get("last_dir", ""))
        if d:
            self.load_folder(d)

    def load_folder(self, d):
        self.source_folder = d
        self.cfg["last_dir"] = d
        save_config(self.cfg)
        self.folder_lbl.setText(d)
        self.reload_files()

    def open_files(self):
        start = self.source_folder or self.cfg.get("last_dir", "")
        exts = " ".join("*" + e for e in sorted(AUDIO_EXT | VIDEO_EXT | IMAGE_EXT))
        paths, _ = QFileDialog.getOpenFileNames(
            self, t("Bestanden openen\u2026", self.lang), start,
            "%s (%s);;%s" % (t("Mediabestanden", self.lang), exts,
                             t("Alle bestanden (*)", self.lang)))
        if not paths:
            return
        self.source_folder = ""
        self.entries = list(paths)
        self.folder_lbl.setText(t("(losse bestanden)", self.lang))
        self._refresh_display()

    def reload_files(self):
        """Vernieuwen: map opnieuw inlezen, of losse lijst opschonen."""
        if self.source_folder:
            ents = []
            try:
                for f in sorted(os.listdir(self.source_folder), key=str.lower):
                    full = os.path.join(self.source_folder, f)
                    if os.path.isfile(full) and kind_of(full) != "other":
                        ents.append(full)
            except Exception:
                pass
            self.entries = ents
        else:
            self.entries = [p for p in self.entries if os.path.isfile(p)]
        self._refresh_display()

    def _refresh_display(self):
        self.list.blockSignals(True)
        self.list.clear()
        flt = self.type_box.currentData() if hasattr(self, "type_box") else "all"
        icons = {"audio": "\u266a  ", "video": "\u25b6  ", "image": "\u25a3  "}
        for full in self.entries:
            k = kind_of(full)
            if k == "other":
                continue
            if flt != "all" and k != flt:
                continue
            it = QListWidgetItem(icons.get(k, "") + os.path.basename(full))
            it.setData(Qt.ItemDataRole.UserRole, full)
            it.setToolTip(full)
            self.list.addItem(it)
        self.list.blockSignals(False)
        self._update_count()
        self._refresh_tags()
        self._update_preview()

    def _selected_paths(self):
        return [it.data(Qt.ItemDataRole.UserRole)
                for it in self.list.selectedItems()]

    def _all_paths(self):
        return [self.list.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(self.list.count())]

    def _on_sel_changed(self):
        self._update_count()
        if self.tabs.currentIndex() == 0:
            self._refresh_tags()
        else:
            self._update_preview()

    def _on_tab(self, idx):
        if idx == 0:
            self._refresh_tags()
        else:
            self._update_preview()

    def _update_count(self):
        n = self.list.count()
        s = len(self.list.selectedItems())
        txt = "%d %s" % (n, t("bestanden", self.lang))
        if s:
            txt += " \u00b7 %d %s" % (s, t("geselecteerd", self.lang))
        self.count_lbl.setText(txt)

    def _apply_fonts(self):
        f = QFont()
        f.setPointSize(self.font_size)
        self.setFont(f)

    # ---- dialogen ----
    def _settings(self):
        dlg = SettingsDialog(self, self.cfg, self.lang)
        if dlg.exec():
            self.cfg = dlg.result_cfg()
            save_config(self.cfg)
            self.font_size = int(self.cfg.get("font_size", 14))
            self._apply_fonts()

    def _guide(self):
        GuideDialog(self, self.lang).exec()

    def _about(self):
        QMessageBox.information(
            self, t("Over", self.lang),
            "%s v%s\n\nMedia-tags bewerken en bulk hernoemen.\nDravenlock\n%s\n%s"
            % (APP_NAME, APP_VERSION, SUPPORT_MAIL, DONATE_URL))


QSS = """
* { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: %(silver)s; }
QMainWindow, QWidget { background: %(bg)s; }
#header { background: %(panel)s; border-bottom: 1px solid %(line)s; }
#title { font-size: 19px; font-weight: 700; color: %(silver)s; }
#ver { color: %(mute)s; font-size: 12px; }
#toolbar { background: %(bg)s; border-bottom: 1px solid %(line)s; }
#sidebar { background: %(panel)s; border-right: 1px solid %(line)s; }
QPushButton { background: %(panel2)s; border: 1px solid #2c2c36; border-radius: 8px;
              padding: 7px 12px; color: %(silver)s; }
QPushButton:hover { border-color: %(accent)s; }
QPushButton:pressed { background: #2a2a33; color: %(silver)s; }
QPushButton:disabled { color: #595962; background: #131318; border-color: #202028; }
QPushButton#primary { background: %(accent)s; color: #08131f; font-weight: 700;
                      border: none; }
QPushButton#primary:hover { background: #87b6e3; }
QPushButton#primary:disabled { background: #2a3a4a; color: #6a7a88; }
QToolButton { background: transparent; border: none; color: %(accent)s; padding: 4px; }
QToolButton#donate { color: %(accent)s; }
QToolButton#ctrl { background: %(panel2)s; border: 1px solid #2c2c36; border-radius: 7px;
                   color: %(silver)s; padding: 4px 8px; font-size: 15px; min-width: 20px; }
QToolButton#ctrl:hover { border-color: %(accent)s; }
QSlider::groove:horizontal { height: 6px; background: %(panel2)s; border-radius: 3px; }
QSlider::sub-page:horizontal { background: %(accent)s; border-radius: 3px; }
QSlider::handle:horizontal { background: %(silver)s; width: 12px; margin: -5px 0;
                             border-radius: 6px; }
QStackedWidget { background: %(panel2)s; border: 1px solid #2c2c36; border-radius: 10px; }
QFrame#sep { color: #2c2c36; }
QLineEdit, QComboBox, QSpinBox { background: %(panel2)s; border: 1px solid #2c2c36;
              border-radius: 8px; padding: 6px 8px; color: %(silver)s; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: %(accent)s; }
QComboBox QAbstractItemView { background: %(panel2)s; color: %(silver)s;
              selection-background-color: %(accent)s; selection-color: #08131f; }
QListWidget#filelist { background: %(panel)s; border: 1px solid %(line)s;
              border-radius: 8px; padding: 4px; outline: none;
              selection-background-color: %(accent)s; selection-color: #08131f; }
QListWidget#filelist::item { padding: 7px 8px; border-radius: 6px; color: %(silver)s; }
QListWidget#filelist::item:selected { background: %(accent)s; color: #08131f; }
QListWidget#filelist::item:hover:!selected { background: %(panel2)s; }
QTabWidget::pane { border: 1px solid %(line)s; border-radius: 8px; top: -1px; }
QTabBar::tab { background: %(panel)s; color: %(mute)s; padding: 8px 16px;
              border: 1px solid %(line)s; border-bottom: none;
              border-top-left-radius: 8px; border-top-right-radius: 8px; }
QTabBar::tab:selected { background: %(panel2)s; color: %(silver)s; }
QTableWidget { background: %(panel)s; border: 1px solid %(line)s; border-radius: 8px;
              gridline-color: %(line)s; }
QTableWidget::item { padding: 4px 6px; color: %(silver)s; }
QHeaderView::section { background: %(panel2)s; color: %(silver)s; padding: 6px;
              border: none; border-bottom: 1px solid %(line)s; font-weight: 600; }
QPlainTextEdit, QTextBrowser#guide { background: %(panel2)s; border: 1px solid #2c2c36;
              border-radius: 8px; padding: 10px; }
QLabel { color: %(silver)s; }
QLabel#preview { background: %(panel2)s; border: 1px solid #2c2c36; border-radius: 10px; }
#muted, #hint { color: %(mute)s; font-size: 12px; }
QDialog { background: %(bg)s; }
QStatusBar { background: %(panel)s; border-top: 1px solid %(line)s; }
QSplitter::handle { background: %(line)s; }
QScrollBar:vertical { background: %(bg)s; width: 12px; }
QScrollBar::handle:vertical { background: #2c2c36; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: %(accent)s; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
""" % {"bg": BG, "panel": PANEL, "panel2": PANEL2, "silver": SILVER,
       "mute": MUTE, "accent": ACCENT, "line": LINE}


def _install_excepthook():
    import traceback

    def hook(exctype, value, tb):
        msg = "".join(traceback.format_exception(exctype, value, tb))
        try:
            with open(os.path.join(_app_dir(), "dravetag-fout.txt"),
                      "w", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
        try:
            if QApplication.instance():
                QMessageBox.critical(None, "DraveTag - fout",
                                     "Er ging iets mis:\n\n" + msg[-1500:]
                                     + "\n\n(Ook opgeslagen in dravetag-fout.txt)")
        except Exception:
            pass
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = hook


def main():
    global _LANG
    _install_excepthook()
    app = QApplication(sys.argv)
    try:
        cfg = load_config()
        _LANG = detect_lang(cfg)
        app.setStyleSheet(QSS)
        win = DraveTag(cfg)
        win.show()
    except Exception:
        sys.excepthook(*sys.exc_info())
        return
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
