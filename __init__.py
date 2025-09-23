##Warning: Use it as your own risk
import random, os, xml.etree.ElementTree as ET 
from aqt import mw 
from aqt.qt import QTimer, QLabel, QPixmap, Qt, QPainter, QGuiApplication
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

config = mw.addonManager.getConfig(__name__)
CHANCE = 1 / 2
FPS = 20
VOLUME_SET = float(config.get("volume", 100))
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
        audio_output.setVolume(VOLUME_SET)
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
    if random.random() < CHANCE:
        play_jumpscare()


timer = QTimer(mw)
timer.timeout.connect(check_random)
timer.start(5000)
