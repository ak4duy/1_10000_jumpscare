## Warning: Use at your own risk
import os
import random
import xml.etree.ElementTree as ET
from fractions import Fraction

from aqt import mw
from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QPainter,
    QPixmap,
    Qt,
    QTimer,
    QUrl,
    QVBoxLayout,
)
from PyQt6.QtMultimedia import QSoundEffect

FPS = 20
ADDON_PATH = os.path.dirname(__file__)
IMAGE_PATH = os.path.join(ADDON_PATH, "foxy.png")
XML_PATH = os.path.join(ADDON_PATH, "foxy.xml")
SOUND_PATH = os.path.join(ADDON_PATH, "jumpscare.wav")

sound_effect = QSoundEffect(mw)
sound_effect.setSource(QUrl.fromLocalFile(SOUND_PATH))

cfg = mw.addonManager.getConfig(__name__)
sound_effect.setVolume(float(cfg.get("volume", 0.5)))
is_playing = False
frames = []


def load_frames():
    global frames
    frames.clear()

    sheet = QPixmap(IMAGE_PATH)
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    for sub in root.findall("SubTexture"):
        x = int(sub.get("x"))
        y = int(sub.get("y"))
        w = int(sub.get("width"))
        h = int(sub.get("height"))

        fx = int(sub.get("frameX", 0))
        fy = int(sub.get("frameY", 0))

        fw = int(sub.get("frameWidth", w))
        fh = int(sub.get("frameHeight", h))

        subimg = sheet.copy(x, y, w, h)

        frame = QPixmap(fw, fh)
        frame.fill(Qt.GlobalColor.transparent)

        painter = QPainter(frame)
        painter.drawPixmap(-fx, -fy, subimg)
        painter.end()

        frames.append(frame)

def play_jumpscare():
    global is_playing
    if is_playing:
        return
    is_playing = True
    if not frames:
        load_frames()
    cfg = mw.addonManager.getConfig(__name__)
    count = int(cfg.get("jumpscare_count", 0)) + 1
    cfg["jumpscare_count"] = count
    mw.addonManager.writeConfig(__name__, cfg)
    
    sound_effect.setVolume(float(cfg.get("volume", 0.5)))
    sound_effect.stop()
    sound_effect.play()

    label = QLabel(mw)
    label.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    label.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    label.setStyleSheet("background-color: transparent;")
    label.setGeometry(mw.rect())
    label.setScaledContents(True)
    label.show()
    label.raise_()

    frame_index = {"i": 0}

    def next_frame():
        global is_playing
        if label.isHidden():
            anim_timer.stop()
            is_playing = False
            return

        if frame_index["i"] < len(frames):
            label.setPixmap(frames[frame_index["i"]])
            frame_index["i"] += 1
        else:
            anim_timer.stop()
            label.close()
            is_playing = False

    anim_timer = QTimer(label)
    anim_timer.timeout.connect(next_frame)
    anim_timer.start(1000 // FPS)
    next_frame()


def check_random():
    if not mw.isActiveWindow():
        return

    cfg = mw.addonManager.getConfig(__name__)
    chance_raw = cfg.get("chance", "1/10000")
    try:
        chance_value = float(Fraction(str(chance_raw).replace(" ", "")))
    except Exception:
        chance_value = 1 / 10000

    if random.random() < chance_value:
        play_jumpscare()


timer = QTimer(mw)
timer.timeout.connect(check_random)
timer.start(1000)


def on_config_button():
    dlg = QDialog(mw)
    dlg.setWindowTitle("1 in 10000 chance of Foxy jumpscare per second")
    layout = QVBoxLayout(dlg)

    cfg = mw.addonManager.getConfig(__name__)

    volume_box = QDoubleSpinBox()
    volume_box.setRange(0.0, 1.0)
    volume_box.setSingleStep(0.1)
    volume_box.setDecimals(2)
    volume_box.setValue(float(cfg.get("volume", 0.5)))
    layout.addWidget(QLabel("Volume (0.0 = mute, 1.0 = max)"))
    layout.addWidget(volume_box)

    chance_edit = QLineEdit()
    chance_edit.setText(str(cfg.get("chance", "1/10000")))
    layout.addWidget(QLabel("Chance per second (e.g. 0.0001 or 1/10000)"))
    layout.addWidget(chance_edit)

    count_label = QLabel()

    def refresh_count():
        cfg = mw.addonManager.getConfig(__name__)
        count_label.setText(f"Total Foxy Jumpscares: {cfg.get('jumpscare_count', 0)}")

    refresh_count()
    layout.addWidget(count_label)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    layout.addWidget(buttons)

    def save_and_close():
        cfg = mw.addonManager.getConfig(__name__)
        cfg["volume"] = float(volume_box.value())
        sound_effect.setVolume(cfg["volume"])
        try:
            text = chance_edit.text().strip()
            chance_value = float(Fraction(text.replace(" ", "")))
            cfg["chance"] = chance_value
        except Exception:
            cfg["chance"] = 1 / 10000

        mw.addonManager.writeConfig(__name__, cfg)
        dlg.accept()

    buttons.accepted.connect(save_and_close)
    buttons.rejected.connect(dlg.reject)

    dlg.exec()


mw.addonManager.setConfigAction(__name__, on_config_button)
