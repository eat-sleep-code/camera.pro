"""
Touchscreen UI for Camera PRO
------------------------------
Full-screen camera viewfinder with translucent overlay controls.

Layout (default 800×600):
  ┌─────────────────────────────────────────────┐
  │  TOP BAR  mode · shutter · iso · ev · wb    │  36px
  ├──────────────────────────────────────────────┤
  │[SS ]│                              │  [●]   │
  │[ISO]│                              │        │
  │[EV ]│        VIEWFINDER            │  [⏹]  │  516px
  │[WB ]│          [AF BOX]            │  [⏱]  │
  │[MTR]│                              │  [☰]  │
  │[BKT]│                              │        │
  ├──────────────────────────────────────────────┤
  │  BOTTOM BAR   📷 PHOTO  🎬 VIDEO   P  M     │  48px
  └─────────────────────────────────────────────┘
  left 64px                       right 64px

Icons via qtawesome (bundles Material Design Icons — no download required).
"""

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QSize, QEvent, QObject
from PySide6.QtGui import (
    QPainter, QPen, QColor, QFont, QPixmap,
    QPainterPath, QBrush,
)
from picamera2 import MappedArray
from actions import Actions
import globals
import os
import sys
import threading
import time

# ---------------------------------------------------------------------------
# Icons via qtawesome (Material Design Icons bundled in the package)
#
# qtawesome calls QFontDatabase.addApplicationFont() at import time, which
# requires a QApplication to already exist.  We import it lazily inside
# get_icon_pixmap() — the first call after QApplication is created in
# Touchscreen.__init__ — so the top-level import never runs early.

_qta = None          # populated on first call to get_icon_pixmap()
_QTA_AVAILABLE = None  # None = not yet checked, True/False after first use

# Logical name → Material Design Icons id (qtawesome 'mdi' set)
_QTA_ICONS = {
    'shutter':  'mdi.camera-iris',
    'iso':      'mdi.iso',
    'ev':       'mdi.brightness-4',
    'wb':       'mdi.white-balance-auto',
    'metering': 'mdi.camera-metering-center',
    'bracket':  'mdi.layers-triple-outline',
    'timer':    'mdi.timer-outline',
    'settings': 'mdi.cog-outline',
    'camera':   'mdi.camera',
    'video':    'mdi.video',
    'stop':     'mdi.stop-circle-outline',
    'plus':     'mdi.plus-circle-outline',
    'minus':    'mdi.minus-circle-outline',
    'af_on':    'mdi.focus-field-horizontal',
    'check':    'mdi.check-circle-outline',
}

# Unicode/text fallbacks used when qtawesome is not installed
_ICON_FALLBACK = {
    'shutter':  'SS',
    'iso':      'ISO',
    'ev':       'EV',
    'wb':       'WB',
    'metering': 'MTR',
    'bracket':  'BKT',
    'timer':    '\u23f1',
    'settings': '\u2699',
    'camera':   '\U0001f4f7',
    'video':    '\u23fa',
    'stop':     '\u23f9',
    'plus':     '+',
    'minus':    '\u2212',
    'af_on':    'AF',
    'check':    '\u2713',
}


def get_icon_pixmap(name: str, size: int = 24, color: QColor = None) -> QPixmap:
    """Return a QPixmap for the named icon.

    qtawesome is imported here (not at module level) so that QApplication
    already exists when qtawesome registers its bundled fonts.
    """
    global _qta, _QTA_AVAILABLE
    if color is None:
        color = C_TEXT
    # Lazy import — safe because QApplication exists by the time any
    # widget calls paintEvent or get_icon_pixmap().
    if _QTA_AVAILABLE is None:
        try:
            import qtawesome as _qta_module
            _qta = _qta_module
            _QTA_AVAILABLE = True
        except ImportError:
            _QTA_AVAILABLE = False
    if _QTA_AVAILABLE and name in _QTA_ICONS:
        try:
            ico = _qta.icon(_QTA_ICONS[name], color=color.name())
            return ico.pixmap(QSize(size, size))
        except Exception:
            pass
    # Fallback: render text into a pixmap
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(color))
    painter.setFont(QFont('sans-serif', max(8, int(size * 0.45))))
    painter.drawText(QRect(0, 0, size, size), Qt.AlignCenter,
                     _ICON_FALLBACK.get(name, name[:3].upper()))
    painter.end()
    return pm


# ---------------------------------------------------------------------------
# Colours / geometry constants

C_BG         = QColor(0, 0, 0, 0)           # fully transparent
C_BAR        = QColor(0, 0, 0, 180)         # top/bottom bars
C_PANEL      = QColor(0, 0, 0, 140)         # side panel background
C_BTN        = QColor(255, 255, 255, 22)    # normal button fill
C_BTN_HOV    = QColor(255, 255, 255, 50)    # hover fill
C_BTN_ACT    = QColor(255, 255, 255, 80)    # active/pressed fill
C_BTN_SEL    = QColor(255, 200, 0, 200)     # selected/on accent (amber)
C_REC        = QColor(220, 40, 40, 255)     # record / danger red
C_PHOTO_RING = QColor(80, 160, 255, 230)    # blue outline on photo button
C_REC_RING   = QColor(220, 50, 50, 230)     # red outline on record button
C_TEXT       = QColor(255, 255, 255, 230)   # primary text
C_TEXT_DIM   = QColor(255, 255, 255, 130)   # secondary / dim text
C_AF_BOX     = QColor(80, 220, 80, 220)     # autofocus box
C_AF_LOCK    = QColor(255, 200, 0, 220)     # AF lock / manual

BAR_H    = 36   # top & bottom bar height
PANEL_W  = 64   # left & right panel width
BTN_H    = 64   # side panel button height
RADIUS   = 12   # button corner radius


# ---------------------------------------------------------------------------
# Reusable overlay widget base

class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAutoFillBackground(False)


# ---------------------------------------------------------------------------
# Flat icon/text button

class CamButton(QWidget):
    """Square icon button with optional label below."""

    def __init__(self, icon_name: str, label: str = '', size: int = BTN_H, parent=None):
        super().__init__(parent)
        self.icon_name = icon_name
        self.label_text = label
        self._size = size
        self._selected = False
        self._hovered = False
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_Hover)
        self.installEventFilter(self)
        self._callback = None
        self._last_press = 0.0   # monotonic time of last accepted press

    def set_callback(self, fn):
        self._callback = fn

    def set_selected(self, val: bool):
        self._selected = val
        self.update()

    def set_label(self, text: str):
        self.label_text = text
        self.update()

    def eventFilter(self, obj, event):
        t = event.type()
        if t == QEvent.HoverEnter:
            self._hovered = True
            self.update()
        elif t == QEvent.HoverLeave:
            self._hovered = False
            self.update()
        elif t == QEvent.MouseButtonPress:
            now = time.monotonic()
            if now - self._last_press >= 0.45:   # 450 ms debounce (FT5506 bounce)
                self._last_press = now
                if self._callback:
                    self._callback()
            return True
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self._size

        # Background pill  (rect from y=4 to y=s-4, i.e. inner height = s-8)
        if self._selected:
            p.setBrush(QBrush(C_BTN_SEL))
        elif self._hovered:
            p.setBrush(QBrush(C_BTN_HOV))
        else:
            p.setBrush(QBrush(C_BTN))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(4, 4, s - 8, s - 8, RADIUS, RADIUS)

        # ── Layout: icon + optional label as a single centred group ──────────
        # The rounded rect inner surface runs from y=4 to y=(s-4).
        # We reserve PAD px of breathing room inside that surface so
        # content never crowds the rounded corners.
        PAD     = 8          # padding from pill edge to content group
        ICN_SZ  = 22         # icon pixel size
        GAP     = 3          # pixels between icon bottom and label top
        LBL_H   = 12         # label text row height (px)

        inner_top = 4 + PAD                          # first usable y inside pill
        inner_h   = (s - 8) - PAD * 2               # usable height  (= s-8-2*PAD)

        if self.label_text:
            content_h = ICN_SZ + GAP + LBL_H
        else:
            content_h = ICN_SZ

        start_y = inner_top + (inner_h - content_h) // 2   # centre the group

        # Icon
        icon_color = QColor(0, 0, 0, 200) if self._selected else C_TEXT
        pm   = get_icon_pixmap(self.icon_name, ICN_SZ, icon_color)
        ix   = (s - ICN_SZ) // 2
        p.drawPixmap(ix, start_y, pm)

        # Label — immediately below the icon with a small gap
        if self.label_text:
            lbl_y = start_y + ICN_SZ + GAP
            p.setFont(QFont('sans-serif', 8))
            p.setPen(QPen(QColor(0, 0, 0, 200) if self._selected else C_TEXT_DIM))
            p.drawText(QRect(2, lbl_y, s - 4, LBL_H + 2), Qt.AlignCenter, self.label_text)

        p.end()


# ---------------------------------------------------------------------------
# Top status bar

class TopBar(OverlayWidget):
    def __init__(self, width: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, BAR_H)
        self._mode = 'P'
        self._shutter = 'Auto'
        self._iso = 'Auto'
        self._ev = '0'
        self._wb = 'Auto'
        self._af = False
        self._recording = False

    def update_state(self):
        s = globals.state
        # Shutter display
        if s.shutter == 0:
            self._shutter = 'Auto'
        elif s.shutter >= 1000000:
            self._shutter = f'{s.shutter // 1000000}"'
        elif s.shutter >= 10000:
            self._shutter = f'1/{1000000 // s.shutter}'
        else:
            self._shutter = f'{s.shutter}\u03bcs'

        # ISO display
        self._iso = 'Auto' if s.iso == 0 else str(s.iso)

        # EV display
        ev = s.exposureValue
        self._ev = ('+' if ev > 0 else '') + str(ev)

        # WB display
        self._wb = s.awbMode

        # Mode
        self._mode = 'M' if s.programMode == 'manual' else 'P'

        # AF
        self._af = globals.primary.hasAutofocus

        # Recording
        self._recording = globals.primary.isRecording

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Bar background
        p.fillRect(0, 0, w, h, C_BAR)

        segments = [
            ('MODE', self._mode, self._mode == 'M'),
            ('SS',   self._shutter, self._shutter != 'Auto'),
            ('ISO',  self._iso,     self._iso != 'Auto'),
            ('EV',   self._ev,      self._ev != '0'),
            ('WB',   self._wb,      self._wb not in ('Auto', 'Disabled')),
        ]

        label_font = QFont('sans-serif', 8)
        value_font = QFont('sans-serif', 11)
        value_font.setBold(True)

        x = 12
        seg_w = 110
        for lbl, val, active in segments:
            # Key label
            p.setFont(label_font)
            p.setPen(QPen(C_TEXT_DIM))
            p.drawText(QRect(x, 2, seg_w, 12), Qt.AlignLeft | Qt.AlignVCenter, lbl)
            # Value
            p.setFont(value_font)
            p.setPen(QPen(C_BTN_SEL if active else C_TEXT))
            p.drawText(QRect(x, 14, seg_w, 18), Qt.AlignLeft | Qt.AlignVCenter, val)
            x += seg_w

        # AF indicator (right side)
        if self._af:
            pm = get_icon_pixmap('af_on', 18, C_AF_BOX)
            p.drawPixmap(w - 76, (h - 18) // 2, pm)
            p.setFont(QFont('sans-serif', 9))
            p.setPen(QPen(C_AF_BOX))
            p.drawText(QRect(w - 54, 0, 36, h), Qt.AlignVCenter | Qt.AlignLeft, 'AF')

        # Recording dot
        if self._recording:
            p.setBrush(QBrush(C_REC))
            p.setPen(Qt.NoPen)
            p.drawEllipse(w - 20, h // 2 - 6, 12, 12)

        p.end()


# ---------------------------------------------------------------------------
# Left panel — exposure controls

class LeftPanel(OverlayWidget):
    def __init__(self, height: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(PANEL_W, height)
        self._actions = Actions()
        self._active_control = None   # name of expanded stepper

        controls = [
            ('shutter',  'SS',  self._on_shutter),
            ('iso',      'ISO', self._on_iso),
            ('ev',       'EV',  self._on_ev),
            ('wb',       'WB',  self._on_wb),
            ('metering', 'MTR', self._on_metering),
            ('bracket',  'BKT', self._on_bracket),
        ]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)

        self._buttons = {}
        for icon, lbl, cb in controls:
            btn = CamButton(icon, lbl, BTN_H, self)
            btn.set_callback(lambda n=icon, fn=cb: self._toggle_stepper(n, fn))
            layout.addWidget(btn, 0, Qt.AlignHCenter)
            self._buttons[icon] = btn

        layout.addStretch()
        self.setLayout(layout)

        # Stepper popup — created lazily on first use so self.parent() is valid.
        self._stepper = None

    def _toggle_stepper(self, name: str, cycle_fn):
        if self._active_control == name:
            self._active_control = None
            if self._stepper:
                self._stepper.hide()
            for b in self._buttons.values():
                b.set_selected(False)
        else:
            # Lazy-create stepper so self.parent() is the QPicamera2 widget
            if self._stepper is None:
                self._stepper = StepperPopup(self.parent())
            self._active_control = name
            for k, b in self._buttons.items():
                b.set_selected(k == name)
            btn = self._buttons[name]
            self._stepper.set_control(name, cycle_fn)
            # Centre the popup on the button using direct geometry arithmetic.
            # self.y() = LeftPanel top inside _preview (= BAR_H)
            # btn.y()  = button top inside LeftPanel (set by QVBoxLayout)
            # Shift up by half the height difference so centres align.
            btn_top_in_preview = self.y() + btn.y()
            popup_y = btn_top_in_preview - (StepperPopup.POPUP_H - BTN_H) // 2 - 3  # -3 px to visually align the popup better with the button
            self._stepper.move(PANEL_W + 4, popup_y)
            self._stepper.show()
            self._stepper.raise_()

    def _on_shutter(self, direction): self._actions.SetShutter(direction)
    def _on_iso(self, direction):     self._actions.SetISO(direction)
    def _on_ev(self, direction):      self._actions.SetExposureValue(direction)
    def _on_wb(self, direction=None): self._actions.SetAWBMode()
    def _on_metering(self, direction=None): self._actions.SetMeteringMode()
    def _on_bracket(self, direction): self._actions.SetBracket(direction)

    def close_stepper(self):
        self._active_control = None
        for b in self._buttons.values():
            b.set_selected(False)
        if self._stepper:
            self._stepper.hide()

    def update_labels(self):
        s = globals.state
        ss_lbl = 'Auto' if s.shutter == 0 else (
            f'1/{1000000 // s.shutter}' if s.shutter >= 10000 else f'{s.shutter}\u03bcs'
        )
        self._buttons['shutter'].set_label(ss_lbl)
        self._buttons['iso'].set_label('Auto' if s.iso == 0 else str(s.iso))
        ev = s.exposureValue
        self._buttons['ev'].set_label(('+' if ev > 0 else '') + str(ev))
        self._buttons['wb'].set_label(s.awbMode[:3])
        metering_short = {'CentreWeighted': 'CTR', 'Spot': 'SPOT', 'Matrix': 'MTX'}
        self._buttons['metering'].set_label(metering_short.get(s.meteringMode, s.meteringMode[:3]))
        self._buttons['bracket'].set_label(f'\u00b1{s.bracket}' if s.bracket else 'Off')


# ---------------------------------------------------------------------------
# Stepper popup (up/down buttons + value readout)

class StepperPopup(OverlayWidget):
    """Small +/- popup that appears beside the active left-panel button."""

    POPUP_W = 220
    POPUP_H = 80
    BTN_SZ  = 68

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.POPUP_W, self.POPUP_H)
        self.hide()
        self._up_fn = None
        self._down_fn = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._down_btn = CamButton('minus', '', self.BTN_SZ, self)
        self._label = QLabel('—', self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet(
            'color: rgba(255,255,255,230); font-size: 17px; font-weight: bold;'
        )
        self._up_btn = CamButton('plus', '', self.BTN_SZ, self)

        layout.addWidget(self._down_btn)
        layout.addWidget(self._label, 1)
        layout.addWidget(self._up_btn)
        self.setLayout(layout)

    def set_control(self, name: str, fn):
        self._current_name = name
        self._down_btn.set_callback(lambda: self._fire(fn, 'down'))
        self._up_btn.set_callback(lambda: self._fire(fn, 'up'))
        self._update_value(name)

    def _fire(self, fn, direction):
        fn(direction)
        self._update_value(self._current_name)

    def _update_from_state(self):
        if hasattr(self, '_current_name'):
            self._update_value(self._current_name)

    def _update_value(self, name: str):
        s = globals.state
        labels = {
            'shutter':  'Auto' if s.shutter == 0 else (
                f'1/{1000000 // s.shutter}' if s.shutter >= 10000 else f'{s.shutter}\u03bcs'),
            'iso':      'Auto' if s.iso == 0 else str(s.iso),
            'ev':       ('+' if s.exposureValue > 0 else '') + str(s.exposureValue),
            'wb':       s.awbMode,
            'metering': {'CentreWeighted': 'Center', 'Spot': 'Spot', 'Matrix': 'Matrix'}.get(s.meteringMode, s.meteringMode),
            'bracket':  'Off' if s.bracket == 0 else f'\u00b1{s.bracket} EV',
        }
        self._label.setText(labels.get(name, '—'))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), C_PANEL)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), RADIUS, RADIUS)
        p.setClipPath(path)
        p.fillRect(self.rect(), C_PANEL)
        p.end()


# ---------------------------------------------------------------------------
# Right panel — capture + secondary controls

class RightPanel(OverlayWidget):
    def __init__(self, height: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(PANEL_W, height)
        self._actions = Actions()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)

        # Photo capture — always captures a still regardless of mode state.
        self._photo_btn = CaptureButton(BTN_H, self)
        self._photo_btn.set_callback(self._on_photo)
        layout.addWidget(self._photo_btn, 0, Qt.AlignHCenter)

        # Video record / stop — tap to start, tap again to stop.
        self._video_btn = RecordButton(BTN_H, self)
        self._video_btn.set_callback(self._on_video)
        layout.addWidget(self._video_btn, 0, Qt.AlignHCenter)

        self._timer_btn = CamButton('timer', 'Off', BTN_H, self)
        self._timer_btn.set_callback(self._on_timer)
        layout.addWidget(self._timer_btn, 0, Qt.AlignHCenter)

        settings_btn = CamButton('settings', '', BTN_H, self)
        settings_btn.set_callback(self._on_settings)
        layout.addWidget(settings_btn, 0, Qt.AlignHCenter)

        layout.addStretch()
        self.setLayout(layout)

    def _on_photo(self):
        globals.state.captureMode = 'photo'
        self._actions.CaptureImage()

    def _on_video(self):
        globals.state.captureMode = 'video'
        self._actions.CaptureVideo()
        self._video_btn.update_state()

    def _on_timer(self):
        self._actions.SetTimer()
        t = globals.state.timer
        self._timer_btn.set_label('Off' if t == 0 else f'{t}s')
        self._timer_btn.set_selected(t > 0)

    def _on_settings(self):
        w = self.window()
        if hasattr(w, 'toggle_settings'):
            w.toggle_settings()

    def update_state(self):
        self._photo_btn.update_state()
        self._video_btn.update_state()
        t = globals.state.timer
        self._timer_btn.set_label('Off' if t == 0 else f'{t}s')
        self._timer_btn.set_selected(t > 0)


# ---------------------------------------------------------------------------
# Large circular capture/record button

class CaptureButton(OverlayWidget):
    """Circular photo-shutter button.  Blue ring; flashes white on press."""

    def __init__(self, size: int = 64, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size      = size
        self._callback  = None
        self._hovered   = False
        self._flashing  = False
        self._last_press = 0.0
        self.setAttribute(Qt.WA_Hover)
        self.installEventFilter(self)

    def set_callback(self, fn):
        self._callback = fn

    def update_state(self):
        self.update()

    def _end_flash(self):
        self._flashing = False
        self.update()

    def eventFilter(self, obj, event):
        t = event.type()
        if t == QEvent.HoverEnter:
            self._hovered = True;  self.update()
        elif t == QEvent.HoverLeave:
            self._hovered = False; self.update()
        elif t == QEvent.MouseButtonPress:
            now = time.monotonic()
            if now - self._last_press >= 2.0:   # 2 s lock — still takes ~1 s
                self._last_press = now
                self._flashing = True
                self.update()
                QTimer.singleShot(160, self._end_flash)
                if self._callback:
                    self._callback()
            return True
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self._size
        cx, cy, r = s // 2, s // 2, s // 2 - 4

        p.setPen(QPen(C_PHOTO_RING, 3))
        if self._flashing:
            p.setBrush(QBrush(QColor(255, 255, 255, 230)))   # bright white flash
        elif self._hovered:
            p.setBrush(QBrush(QColor(255, 255, 255, 70)))
        else:
            p.setBrush(QBrush(QColor(255, 255, 255, 35)))

        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        icon_col = QColor(0, 0, 0, 180) if self._flashing else QColor(255, 255, 255, 230)
        pm = get_icon_pixmap('camera', 28, icon_col)
        p.drawPixmap((s - pm.width()) // 2, (s - pm.height()) // 2, pm)
        p.end()


# ---------------------------------------------------------------------------
# Circular video record / stop button

class RecordButton(OverlayWidget):
    """Red-ringed circle button. Blinks red while recording."""

    BLINK_MS = 500   # blink half-period in milliseconds

    def __init__(self, size: int = 64, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size      = size
        self._callback  = None
        self._hovered   = False
        self._blink_on  = True
        self._last_press = 0.0
        self.setAttribute(Qt.WA_Hover)
        self.installEventFilter(self)

        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(self.BLINK_MS)
        self._blink_timer.timeout.connect(self._tick_blink)

    def set_callback(self, fn):
        self._callback = fn

    def _tick_blink(self):
        self._blink_on = not self._blink_on
        self.update()

    def update_state(self):
        if globals.primary.isRecording:
            if not self._blink_timer.isActive():
                self._blink_on = True
                self._blink_timer.start()
        else:
            self._blink_timer.stop()
            self._blink_on = True
        self.update()

    def eventFilter(self, obj, event):
        t = event.type()
        if t == QEvent.HoverEnter:
            self._hovered = True;  self.update()
        elif t == QEvent.HoverLeave:
            self._hovered = False; self.update()
        elif t == QEvent.MouseButtonPress:
            now = time.monotonic()
            # Shorter cooldown when stopping so it feels responsive
            cooldown = 0.6 if globals.primary.isRecording else 1.5
            if now - self._last_press >= cooldown:
                self._last_press = now
                if self._callback:
                    self._callback()
            return True
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s  = self._size
        cx, cy, r = s // 2, s // 2, s // 2 - 4

        recording = globals.primary.isRecording

        if recording:
            # Blinking red fill
            fill = C_REC if self._blink_on else C_REC.darker(170)
            p.setPen(QPen(C_REC_RING, 3))
            p.setBrush(QBrush(fill))
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            pm = get_icon_pixmap('stop', 26, QColor(255, 255, 255))
        else:
            # Dark fill, red ring
            fill_alpha = 60 if self._hovered else 30
            p.setPen(QPen(C_REC_RING, 3))
            p.setBrush(QBrush(QColor(255, 255, 255, fill_alpha)))
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            pm = get_icon_pixmap('video', 26, QColor(255, 255, 255, 210))

        p.drawPixmap((s - pm.width()) // 2, (s - pm.height()) // 2, pm)
        p.end()


# ---------------------------------------------------------------------------
# AF focus box overlay

class FocusBox(OverlayWidget):
    CORNER = 14   # length of each corner bracket arm
    THICK  = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._visible = False
        self._locked = False    # True = AF locked (amber colour)
        self._rect = QRect(0, 0, 80, 60)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_focus_rect(self, rect: QRect, locked: bool = False):
        self._rect = rect
        self._locked = locked
        self._visible = True
        self.update()

    def hide_box(self):
        self._visible = False
        self.update()

    def paintEvent(self, event):
        if not self._visible:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        colour = C_AF_LOCK if self._locked else C_AF_BOX
        pen = QPen(colour, self.THICK)
        p.setPen(pen)
        r = self._rect
        c = self.CORNER
        x, y, w, h = r.x(), r.y(), r.width(), r.height()

        # Draw four corner brackets
        for px, py, dx, dy in [
            (x,     y,     1,  1),   # top-left
            (x+w,   y,    -1,  1),   # top-right
            (x,     y+h,   1, -1),   # bottom-left
            (x+w,   y+h,  -1, -1),   # bottom-right
        ]:
            p.drawLine(px, py, px + dx * c, py)
            p.drawLine(px, py, px, py + dy * c)

        p.end()


# ---------------------------------------------------------------------------
# Bottom mode bar

class _BtnTapFilter(QObject):
    """Event filter that gives any QWidget a debounced tap callback.

    QPushButton inside an OverlayWidget (WA_TranslucentBackground +
    WA_NoSystemBackground) can be skipped by Qt's touch-synthesis hit-test.
    Installing this filter directly on the button bypasses that problem.
    """
    def __init__(self, widget: QWidget, fn, parent=None):
        super().__init__(parent)
        self._fn  = fn
        self._last = 0.0
        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            now = time.monotonic()
            if now - self._last >= 0.45:
                self._last = now
                self._fn()
            return True
        return False


class BottomBar(OverlayWidget):
    def __init__(self, width: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, BAR_H + 12)
        self._filters = []   # keep filter objects alive

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(8)

        self._photo_btn = self._mode_btn('photo', 'PHOTO')
        self._video_btn = self._mode_btn('video', 'VIDEO')

        layout.addWidget(self._photo_btn)
        layout.addWidget(self._video_btn)
        layout.addStretch()

        self._p_btn = self._prog_btn('P', 'auto')
        self._m_btn = self._prog_btn('M', 'manual')

        layout.addWidget(self._p_btn)
        layout.addWidget(self._m_btn)

        self.setLayout(layout)
        self._mode_changed_cb = None   # set by CameraWindow after construction
        self._refresh()

    def set_mode_changed_callback(self, fn):
        """Called by CameraWindow so it can update the capture button immediately."""
        self._mode_changed_cb = fn

    def _mode_btn(self, mode: str, label: str) -> QPushButton:
        btn = QPushButton(f'  {label}', self)
        btn.setObjectName(f'modeBtn_{mode}')
        btn.setFixedHeight(36)
        btn.setFont(QFont('sans-serif', 10))
        f = _BtnTapFilter(btn, lambda m=mode: self._set_capture_mode(m), btn)
        self._filters.append(f)
        return btn

    def _prog_btn(self, label: str, mode: str) -> QPushButton:
        btn = QPushButton(label, self)
        btn.setObjectName(f'progBtn_{mode}')
        btn.setFixedSize(40, 36)
        btn.setFont(QFont('sans-serif', 11))
        f = _BtnTapFilter(btn, lambda m=mode: self._set_program_mode(m), btn)
        self._filters.append(f)
        return btn

    def _set_capture_mode(self, mode: str):
        globals.state.captureMode = mode
        self._refresh()
        if self._mode_changed_cb:
            self._mode_changed_cb()

    def _set_program_mode(self, mode: str):
        globals.state.programMode = mode
        self._refresh()

    def _refresh(self):
        cm = globals.state.captureMode
        pm = globals.state.programMode
        self._photo_btn.setProperty('selected', cm == 'photo')
        self._video_btn.setProperty('selected', cm == 'video')
        self._p_btn.setProperty('selected', pm == 'auto')
        self._m_btn.setProperty('selected', pm == 'manual')
        for w in [self._photo_btn, self._video_btn, self._p_btn, self._m_btn]:
            w.style().unpolish(w)
            w.style().polish(w)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), C_BAR)
        p.end()


# ---------------------------------------------------------------------------
# Main camera window

class CameraWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

        W = globals.preview.width
        H = globals.preview.height
        self._W = W
        self._H = H

        # Use a plain QLabel as the viewfinder surface.
        # This avoids QPicamera2 / QGlPicamera2 entirely — no EGL, no
        # platform-plugin dependency.  Camera frames are delivered via
        # picamera2's pre_callback into a thread-safe buffer and painted
        # into the label by a QTimer every ~33 ms.
        self._preview = QLabel(self)
        self._preview.setFixedSize(W, H)
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setStyleSheet('background: black;')
        self.setCentralWidget(self._preview)

        # Thread-safe frame buffer — written by camera thread, read by Qt thread.
        self._frame_lock = threading.Lock()
        self._latest_frame = None

        def _on_camera_frame(request):
            with MappedArray(request, 'main') as m:
                with self._frame_lock:
                    self._latest_frame = m.array.copy()

        # Configure and start the camera.
        globals.primary.module.configure(globals.primary.previewConfiguration)
        globals.primary.module.pre_callback = _on_camera_frame
        globals.primary.module.start()

        # Enable continuous AF now that the camera is running.
        if globals.primary.hasAutofocus:
            try:
                from libcamera import controls as lc
                globals.primary.module.set_controls(
                    {"AfMode": lc.AfModeEnum.Continuous}
                )
            except Exception:
                pass

        vp_y = BAR_H
        vp_h = H - BAR_H * 2 - 12

        # All overlays are children of self._preview — normal QWidget children
        # render on top of the label's pixmap with no compositing issues.
        self._top_bar = TopBar(W, self._preview)
        self._top_bar.setGeometry(0, 0, W, BAR_H)
        self._top_bar.raise_()

        self._left = LeftPanel(vp_h, self._preview)
        self._left.setGeometry(0, vp_y, PANEL_W, vp_h)
        self._left.raise_()

        self._right = RightPanel(vp_h, self._preview)
        self._right.setGeometry(W - PANEL_W, vp_y, PANEL_W, vp_h)
        self._right.raise_()

        self._focus_box = FocusBox(self._preview)
        self._focus_box.setGeometry(PANEL_W, vp_y, W - PANEL_W * 2, vp_h)
        self._focus_box.raise_()

        if globals.primary.hasAutofocus:
            fw, fh = 80, 60
            cx = (W - PANEL_W * 2) // 2 - fw // 2
            cy = vp_h // 2 - fh // 2
            self._focus_box.set_focus_rect(QRect(cx, cy, fw, fh))

        self._bottom = BottomBar(W, self._preview)
        self._bottom.setGeometry(0, H - BAR_H - 12, W, BAR_H + 12)
        self._bottom.raise_()
        self._bottom.set_mode_changed_callback(self._right.update_state)

        self._settings_panel = SettingsPanel(W // 2, vp_h, self._preview)
        self._settings_panel.setGeometry(W // 4, vp_y, W // 2, vp_h)
        self._settings_panel.hide()
        self._settings_panel.raise_()

        # Install an event filter on _preview to handle viewfinder taps
        # (used for AF point selection when hasAutofocus is True).
        self._preview.installEventFilter(self)

        # Frame paint timer (~30 fps)
        self._frame_timer = QTimer(self)
        self._frame_timer.timeout.connect(self._paint_frame)
        self._frame_timer.start(33)

        # UI label refresh timer (500 ms)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_ui)
        self._timer.start(500)

    def _paint_frame(self):
        """Copy the latest camera frame into the preview QLabel."""
        with self._frame_lock:
            frame = self._latest_frame
        if frame is None:
            return
        try:
            from PySide6.QtGui import QImage
            h, w = frame.shape[:2]
            stride = frame.strides[0]
            # picamera2 preview default is BGR888; swap to RGB for QImage
            fmt = QImage.Format_RGB888
            if frame.shape[2] == 4:
                fmt = QImage.Format_RGBX8888
            qimg = QImage(frame.data, w, h, stride, fmt).rgbSwapped()
            self._preview.setPixmap(
                QPixmap.fromImage(qimg).scaled(
                    self._W, self._H, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        except Exception:
            pass

    def _on_viewfinder_tap(self, event):
        if not globals.primary.hasAutofocus:
            return
        x = event.position().x() - PANEL_W
        y = event.position().y() - BAR_H
        fw, fh = 80, 60
        rect = QRect(int(x) - fw // 2, int(y) - fh // 2, fw, fh)
        self._focus_box.set_focus_rect(rect)
        # Trigger AF on the tapped region (picamera2 AfWindows control)
        try:
            from libcamera import controls as lc
            fx = event.position().x() / self._W
            fy = (event.position().y() - BAR_H) / (self._H - BAR_H * 2 - 12)
            w_norm, h_norm = 80 / self._W, 60 / (self._H - BAR_H * 2 - 12)
            globals.primary.module.set_controls({
                "AfMode":    lc.AfModeEnum.Auto,
                "AfWindows": [(fx - w_norm / 2, fy - h_norm / 2, w_norm, h_norm)],
                "AfTrigger": lc.AfTriggerEnum.Start,
            })
        except Exception:
            pass

    def _on_viewfinder_touch(self, event):
        """Handle raw touch on the viewfinder (fallback when synthesis is off)."""
        if event.type() == QEvent.TouchBegin:
            pts = event.points() if hasattr(event, 'points') else event.touchPoints()
            if pts:
                pos = pts[0].position() if hasattr(pts[0], 'position') else pts[0].pos()
                # Reuse the mouse-tap handler logic via a synthetic QMouseEvent
                class _FakeEvent:
                    def position(self_):
                        return pos
                self._on_viewfinder_tap(_FakeEvent())
            event.accept()

    def _refresh_ui(self):
        self._top_bar.update_state()
        self._left.update_labels()
        self._right.update_state()

    def toggle_settings(self):
        if self._settings_panel.isVisible():
            self._settings_panel.hide()
        else:
            self._settings_panel.show()
            self._settings_panel.raise_()

    def eventFilter(self, obj, event):
        """Catch mouse presses on the viewfinder QLabel for AF point selection."""
        if obj is self._preview and event.type() == QEvent.MouseButtonPress:
            self._on_viewfinder_tap(event)
            return False   # don't consume — let children still receive it
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self._settings_panel.isVisible():
                self._settings_panel.hide()
            elif self._left._active_control:
                self._left.close_stepper()


# ---------------------------------------------------------------------------
# Settings panel (slides over the viewfinder)

class SettingsPanel(OverlayWidget):
    """Full-height overlay panel for camera settings."""

    _ROW_H   = 52    # height of each setting row
    _LBL_SZ  = 13    # key label font size
    _VAL_SZ  = 16    # value / button font size

    def __init__(self, width: int, height: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._actions = Actions()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(0)

        # ── Title ──────────────────────────────────────────────────────────
        title = QLabel('⚙  Settings', self)
        title.setStyleSheet(
            'color: white; font-size: 20px; font-weight: bold; padding-bottom: 10px;'
        )
        outer.addWidget(title)

        sep = QFrame(self)
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet('color: rgba(255,255,255,40);')
        outer.addWidget(sep)
        outer.addSpacing(6)

        # ── Setting rows ───────────────────────────────────────────────────
        self._rows: dict[str, QLabel] = {}

        rows = [
            ('Exposure',  self._cycle_exposure),
            ('Metering',  self._cycle_metering),
            ('White Bal', self._cycle_wb),
            ('Program',   self._cycle_program),
            ('Timer',     self._cycle_timer),
        ]

        for key, fn in rows:
            row_widget = QWidget(self)
            row_widget.setFixedHeight(self._ROW_H)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            key_lbl = QLabel(key, row_widget)
            key_lbl.setStyleSheet(
                f'color: rgba(255,255,255,160); font-size: {self._LBL_SZ}px;'
            )
            key_lbl.setFixedWidth(80)

            val_btn = QPushButton('—', row_widget)
            val_btn.setObjectName('settingsVal')
            val_btn.setStyleSheet(
                f'background: rgba(255,255,255,0.12); color: white; '
                f'font-size: {self._VAL_SZ}px; font-weight: 600; '
                f'border-radius: 8px; padding: 6px 14px; text-align: left;'
            )
            val_btn.clicked.connect(fn)
            self._rows[key] = val_btn

            row_layout.addWidget(key_lbl)
            row_layout.addWidget(val_btn, 1)
            outer.addWidget(row_widget)
            outer.addSpacing(2)

        outer.addStretch()

        # ── Close ──────────────────────────────────────────────────────────
        close_btn = QPushButton('✕  Close', self)
        close_btn.setObjectName('settingsClose')
        close_btn.setFixedHeight(48)
        close_btn.setStyleSheet(
            'background: rgba(255,255,255,0.15); color: white; '
            'font-size: 16px; font-weight: 600; border-radius: 10px;'
        )
        close_btn.clicked.connect(self.hide)
        outer.addWidget(close_btn)

        self.setLayout(outer)
        self.refresh()

    # ── Value cycling ───────────────────────────────────────────────────────

    def _cycle_exposure(self):
        self._actions.SetExposureMode()
        self.refresh()

    def _cycle_metering(self):
        self._actions.SetMeteringMode()
        self.refresh()

    def _cycle_wb(self):
        self._actions.SetAWBMode()
        self.refresh()

    def _cycle_program(self):
        s = globals.state
        s.programMode = 'manual' if s.programMode == 'auto' else 'auto'
        self.refresh()

    def _cycle_timer(self):
        self._actions.SetTimer()
        self.refresh()

    # ── Refresh displayed values ────────────────────────────────────────────

    def refresh(self):
        s = globals.state
        timer_val = 'Off' if s.timer == 0 else f'{s.timer} s'
        values = {
            'Exposure':  s.exposureMode,
            'Metering':  {'CentreWeighted': 'Center', 'Spot': 'Spot',
                          'Matrix': 'Matrix'}.get(s.meteringMode, s.meteringMode),
            'White Bal': s.awbMode,
            'Program':   'Auto (P)' if s.programMode == 'auto' else 'Manual (M)',
            'Timer':     timer_val,
        }
        for key, val_btn in self._rows.items():
            val_btn.setText(values.get(key, '—'))

    def showEvent(self, event):
        self.refresh()
        super().showEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        p.fillPath(path, QColor(10, 10, 25, 235))
        p.setPen(QPen(QColor(255, 255, 255, 40), 1))
        p.drawPath(path)
        p.end()


# ---------------------------------------------------------------------------
# Touch device auto-detection
#
# Qt's evdevtouch plugin scans /dev/input/event* for touch devices when no
# explicit path is given via QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS.  On some
# Pi display drivers (e.g. FT5406 / GT911) the device doesn't advertise
# BTN_TOUCH in its capabilities, so Qt's scanner may miss it.  We probe
# sysfs here and pin the device path explicitly if we find one.

def _find_touch_device() -> str | None:
    """Return '/dev/input/eventN' for the first capacitive touch controller
    found in sysfs, or None if nothing is found / already overridden."""
    if 'QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS' in os.environ:
        return None   # caller already specified it

    import glob as _glob
    # Walk /sys/class/input looking for a device whose name suggests touch
    touch_keywords = ('touch', 'ft5', 'gt9', 'goodix', 'edt-ft', 'ilitek')
    for name_path in _glob.glob('/sys/class/input/*/device/name'):
        try:
            with open(name_path) as f:
                name = f.read().strip().lower()
        except OSError:
            continue
        if any(k in name for k in touch_keywords):
            # e.g. /sys/class/input/event0/device/name  →  /dev/input/event0
            event_dir = name_path.replace('/device/name', '')
            event_name = os.path.basename(event_dir)
            dev_path = f'/dev/input/{event_name}'
            if os.path.exists(dev_path):
                return dev_path
    return None


# ---------------------------------------------------------------------------
# Entry point

class Touchscreen:
    def __init__(self):
        # QApplication is created in camera.py before any imports run.
        # Retrieve the existing instance — never create a second one.
        app = QApplication.instance()

        # Ensure Qt synthesises mouse events from unhandled touch events so
        # that all our MouseButtonPress-based widgets work without requiring
        # explicit touch-event handling in every widget.
        app.setAttribute(Qt.ApplicationAttribute.AA_SynthesizeMouseForUnhandledTouchEvents, True)

        # Pin the evdev touch device path if auto-detection failed.
        dev = _find_touch_device()
        if dev:
            os.environ['QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS'] = dev

        # Load stylesheet
        qss_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'style.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r') as f:
                app.setStyleSheet(f.read())

        self._window = CameraWindow()
        self._window.showFullScreen()

        app.exec()
