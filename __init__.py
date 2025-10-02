## Warning: Use it as your own risk
import random, os, xml.etree.ElementTree as ET
from aqt import mw
from aqt.qt import (
    QTimer, QLabel, QPixmap, Qt, QPainter, QUrl,
    QVBoxLayout, QDialog, QDialogButtonBox, QLineEdit, QDoubleSpinBox
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from fractions import Fraction

cfg = mw.addonManager.getConfig(__name__)
chance_raw = cfg.get("chance", "1/10000")

try:
    CHANCE = float(Fraction(str(chance_raw).replace(" ", "")))
except Exception:
    CHANCE = 1/10000

FPS = 20
ADDON_PATH = os.path.dirname(__file__)
IMAGE_PATH = os.path.join(ADDON_PATH, "foxy.png")
XML_PATH = os.path.join(ADDON_PATH, "foxy.xml")
SOUND_PATH = os.path.join(ADDON_PATH, "jumpscare.mp3")

player = None
audio_output = None
frames = []


def load_frames():
    global frames
    frames.clear()

    sheet = QPixmap(IMAGE_PATH)
    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    for sub in root.findall("SubTexture"):
        x, y = int(sub.get("x")), int(sub.get("y"))
        w, h = int(sub.get("width")), int(sub.get("height"))
        fx, fy = int(sub.get("frameX", 0)), int(sub.get("frameY", 0))
        fw, fh = int(sub.get("frameWidth", w)), int(sub.get("frameHeight", h))

        subimg = sheet.copy(x, y, w, h)

        frame = QPixmap(fw, fh)
        frame.fill(Qt.GlobalColor.transparent)

        painter = QPainter(frame)

        painter.drawPixmap(-fx, -fy, subimg)
        painter.end()

        frames.append(frame)


def play_jumpscare():
    global player, audio_output
    if not frames:
        load_frames()
        cfg = mw.addonManager.getConfig(__name__)
        count = int(cfg.get("jumpscare_count", 0)) + 1
        cfg["jumpscare_count"] = count
        mw.addonManager.writeConfig(__name__, cfg)

    label = QLabel(mw)
    label.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    label.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    label.setStyleSheet("background-color: transparent;")
    label.setGeometry(mw.rect())
    label.setScaledContents(True)
    label.show()

    try:
        player = QMediaPlayer()
        audio_output = QAudioOutput()
        player.setAudioOutput(audio_output)
        player.setSource(QUrl.fromLocalFile(SOUND_PATH))
        cfg = mw.addonManager.getConfig(__name__)
        audio_output.setVolume(float(cfg.get("volume", 1)))
        player.play()
    except Exception as e:
        print("Sound error:", e)

    frame_index = {"i": 0}

    def next_frame():
        if frame_index["i"] < len(frames):
            f = frames[frame_index["i"]]
            label.setPixmap(f.scaled(
                mw.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            frame_index["i"] += 1
        else:
            label.close()

    anim_timer = QTimer(mw)
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
    volume_box.setValue(float(cfg.get("volume", 1.0)))
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

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    layout.addWidget(buttons)

    def save_and_close():
        cfg = mw.addonManager.getConfig(__name__)
        cfg["volume"] = float(volume_box.value())

        try:
            text = chance_edit.text().strip()
            chance_value = float(Fraction(text))
            cfg["chance"] = chance_value
        except Exception:
            cfg["chance"] = 1 / 10000

        mw.addonManager.writeConfig(__name__, cfg)
        dlg.accept()

    buttons.accepted.connect(save_and_close)
    buttons.rejected.connect(dlg.reject)

    dlg.exec()


mw.addonManager.setConfigAction(__name__, on_config_button)