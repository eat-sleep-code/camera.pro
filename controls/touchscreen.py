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
from PySide6.QtCore import Qt, QTimer, QRect, QPoint, QSize, QEvent
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

C_BG       = QColor(0, 0, 0, 0)           # fully transparent
C_BAR      = QColor(0, 0, 0, 180)         # top/bottom bars
C_PANEL    = QColor(0, 0, 0, 140)         # side panel background
C_BTN      = QColor(255, 255, 255, 22)    # normal button fill
C_BTN_HOV  = QColor(255, 255, 255, 50)    # hover fill
C_BTN_ACT  = QColor(255, 255, 255, 80)    # active/pressed fill
C_BTN_SEL  = QColor(255, 200, 0, 200)     # selected/on accent (amber)
C_REC      = QColor(220, 40, 40, 255)     # record button
C_TEXT     = QColor(255, 255, 255, 230)   # primary text
C_TEXT_DIM = QColor(255, 255, 255, 130)   # secondary / dim text
C_AF_BOX   = QColor(80, 220, 80, 220)     # autofocus box
C_AF_LOCK  = QColor(255, 200, 0, 220)     # AF lock / manual

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

    def set_callback(self, fn):
        self._callback = fn

    def set_selected(self, val: bool):
        self._selected = val
        self.update()

    def set_label(self, text: str):
        self.label_text = text
        self.update()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.HoverEnter:
            self._hovered = True
            self.update()
        elif event.type() == QEvent.HoverLeave:
            self._hovered = False
            self.update()
        elif event.type() == QEvent.MouseButtonPress:
            if self._callback:
                self._callback()
            return True
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self._size

        # Background pill
        if self._selected:
            p.setBrush(QBrush(C_BTN_SEL))
        elif self._hovered:
            p.setBrush(QBrush(C_BTN_HOV))
        else:
            p.setBrush(QBrush(C_BTN))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(4, 4, s - 8, s - 8, RADIUS, RADIUS)

        # Icon
        icon_size = 26
        icon_color = QColor(0, 0, 0, 200) if self._selected else C_TEXT
        pm = get_icon_pixmap(self.icon_name, icon_size, icon_color)
        icon_y = 6 if self.label_text else (s - icon_size) // 2
        icon_x = (s - icon_size) // 2
        p.drawPixmap(icon_x, icon_y, pm)

        # Sub-label (lower strip)
        if self.label_text:
            p.setFont(QFont('sans-serif', 8))
            p.setPen(QPen(QColor(0, 0, 0, 200) if self._selected else C_TEXT_DIM))
            p.drawText(QRect(0, s - 16, s, 14), Qt.AlignCenter, self.label_text)

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
        layout.setSpacing(4)

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
        else:
            # Lazy-create stepper so self.parent() is the QPicamera2 widget
            if self._stepper is None:
                self._stepper = StepperPopup(self.parent())
            self._active_control = name
            for k, b in self._buttons.items():
                b.set_selected(k == name)
            btn = self._buttons[name]
            btn_pos = btn.mapTo(self.parent(), QPoint(0, 0))
            self._stepper.set_control(name, cycle_fn)
            self._stepper.move(self.x() + PANEL_W + 4, btn_pos.y())
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, BTN_H)
        self.hide()
        self._up_fn = None
        self._down_fn = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self._down_btn = CamButton('minus', '', 48, self)
        self._label = QLabel('—', self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet('color: rgba(255,255,255,220); font-size: 14px; font-weight: bold;')
        self._up_btn = CamButton('plus', '', 48, self)

        layout.addWidget(self._down_btn)
        layout.addWidget(self._label, 1)
        layout.addWidget(self._up_btn)
        self.setLayout(layout)

    def set_control(self, name: str, fn):
        self._down_btn.set_callback(lambda: self._fire(fn, 'down'))
        self._up_btn.set_callback(lambda: self._fire(fn, 'up'))
        self._update_value(name)

    def _fire(self, fn, direction):
        fn(direction)
        # Re-read value from state
        self._update_from_state()

    def _update_from_state(self):
        # Refresh label after any action
        self.update()

    def _update_value(self, name: str):
        s = globals.state
        labels = {
            'shutter':  'Auto' if s.shutter == 0 else (
                f'1/{1000000 // s.shutter}' if s.shutter >= 10000 else f'{s.shutter}\u03bcs'),
            'iso':      'Auto' if s.iso == 0 else str(s.iso),
            'ev':       ('+' if s.exposureValue > 0 else '') + str(s.exposureValue),
            'wb':       s.awbMode,
            'metering': {'CentreWeighted': 'Centre', 'Spot': 'Spot', 'Matrix': 'Matrix'}.get(s.meteringMode, s.meteringMode),
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
        layout.setSpacing(4)

        self._capture_btn = CaptureButton(BTN_H, self)
        self._capture_btn.set_callback(self._on_capture)
        layout.addWidget(self._capture_btn, 0, Qt.AlignHCenter)

        timer_btn = CamButton('timer', 'Off', BTN_H, self)
        timer_btn.set_callback(self._on_timer)
        self._timer_btn = timer_btn
        layout.addWidget(timer_btn, 0, Qt.AlignHCenter)

        settings_btn = CamButton('settings', '', BTN_H, self)
        settings_btn.set_callback(self._on_settings)
        layout.addWidget(settings_btn, 0, Qt.AlignHCenter)

        layout.addStretch()
        self.setLayout(layout)

    def _on_capture(self):
        if globals.state.captureMode == 'video':
            self._actions.CaptureVideo()
        else:
            self._actions.CaptureImage()
        self._capture_btn.update_state()

    def _on_timer(self):
        self._actions.SetTimer()
        t = globals.state.timer
        self._timer_btn.set_label('Off' if t == 0 else f'{t}s')
        self._timer_btn.set_selected(t > 0)

    def _on_settings(self):
        # Signal the main window to toggle settings panel
        w = self.window()
        if hasattr(w, 'toggle_settings'):
            w.toggle_settings()

    def update_state(self):
        self._capture_btn.update_state()
        t = globals.state.timer
        self._timer_btn.set_label('Off' if t == 0 else f'{t}s')
        self._timer_btn.set_selected(t > 0)


# ---------------------------------------------------------------------------
# Large circular capture/record button

class CaptureButton(OverlayWidget):
    def __init__(self, size: int = 64, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        self._callback = None
        self._hovered = False
        self.setAttribute(Qt.WA_Hover)
        self.installEventFilter(self)

    def set_callback(self, fn):
        self._callback = fn

    def update_state(self):
        self.update()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.HoverEnter:
            self._hovered = True; self.update()
        elif event.type() == QEvent.HoverLeave:
            self._hovered = False; self.update()
        elif event.type() == QEvent.MouseButtonPress:
            if self._callback:
                self._callback()
            return True
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        s = self._size
        cx, cy, r = s // 2, s // 2, s // 2 - 4

        is_video = globals.state.captureMode == 'video'
        is_recording = globals.primary.isRecording

        if is_recording:
            p.setPen(QPen(C_BTN_SEL, 3))
            p.setBrush(QBrush(C_REC.darker(120) if self._hovered else C_REC))
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            pm = get_icon_pixmap('stop', 28, QColor(255, 255, 255))
        elif is_video:
            p.setPen(QPen(QColor(255, 255, 255, 60), 2))
            p.setBrush(QBrush(C_REC.darker(130) if self._hovered else C_REC))
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            pm = get_icon_pixmap('video', 28, QColor(255, 255, 255))
        else:
            p.setPen(QPen(QColor(255, 255, 255, 200), 3))
            p.setBrush(QBrush(QColor(255, 255, 255, 80 if self._hovered else 40)))
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            pm = get_icon_pixmap('camera', 28, QColor(255, 255, 255, 230))

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

class BottomBar(OverlayWidget):
    def __init__(self, width: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, BAR_H + 12)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        self._photo_btn = self._mode_btn('photo', 'camera', 'PHOTO')
        self._video_btn = self._mode_btn('video', 'video', 'VIDEO')

        layout.addWidget(self._photo_btn)
        layout.addWidget(self._video_btn)
        layout.addStretch()

        self._p_btn = self._prog_btn('P', 'auto')
        self._m_btn = self._prog_btn('M', 'manual')

        layout.addWidget(self._p_btn)
        layout.addWidget(self._m_btn)

        self.setLayout(layout)
        self._refresh()

    def _mode_btn(self, mode: str, icon: str, label: str) -> QPushButton:
        btn = QPushButton(f'  {label}', self)
        btn.setObjectName(f'modeBtn_{mode}')
        btn.setFixedHeight(36)
        btn.setFont(QFont('sans-serif', 10))
        btn.clicked.connect(lambda: self._set_capture_mode(mode))
        return btn

    def _prog_btn(self, label: str, mode: str) -> QPushButton:
        btn = QPushButton(label, self)
        btn.setObjectName(f'progBtn_{mode}')
        btn.setFixedSize(40, 36)
        btn.setFont(QFont('sans-serif', 11))
        btn.clicked.connect(lambda: self._set_program_mode(mode))
        return btn

    def _set_capture_mode(self, mode: str):
        globals.state.captureMode = mode
        self._refresh()

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
        # Force style refresh
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

        self._settings_panel = SettingsPanel(W // 2, vp_h, self._preview)
        self._settings_panel.setGeometry(W // 4, vp_y, W // 2, vp_h)
        self._settings_panel.hide()
        self._settings_panel.raise_()

        self._preview.mousePressEvent = self._on_viewfinder_tap

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self._settings_panel.isVisible():
                self._settings_panel.hide()
            elif self._left._active_control:
                self._left.close_stepper()


# ---------------------------------------------------------------------------
# Settings panel (slides over the viewfinder)

class SettingsPanel(OverlayWidget):
    def __init__(self, width: int, height: int, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel('Settings', self)
        title.setStyleSheet('color: white; font-size: 16px; font-weight: bold;')
        layout.addWidget(title)

        for label_text, action in [
            ('Exposure Mode',  'exposureMode'),
            ('Metering Mode',  'meteringMode'),
            ('AWB Mode',       'awbMode'),
            ('Timer',          'timer'),
        ]:
            lbl = QLabel(label_text, self)
            lbl.setStyleSheet('color: rgba(255,255,255,160); font-size: 11px;')
            layout.addWidget(lbl)

        layout.addStretch()

        close_btn = QPushButton('Close', self)
        close_btn.setObjectName('settingsClose')
        close_btn.clicked.connect(lambda: self.hide())
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        p.fillPath(path, QColor(10, 10, 20, 220))
        p.setPen(QPen(QColor(255, 255, 255, 30), 1))
        p.drawPath(path)
        p.end()


# ---------------------------------------------------------------------------
# Entry point

class Touchscreen:
    def __init__(self):
        # QApplication is created in camera.py before any imports run.
        # Retrieve the existing instance — never create a second one.
        app = QApplication.instance()

        # Load stylesheet
        qss_path = os.path.join(os.path.dirname(__file__), '..', 'ui', 'style.qss')
        if os.path.exists(qss_path):
            with open(qss_path, 'r') as f:
                app.setStyleSheet(f.read())

        self._window = CameraWindow()
        self._window.showFullScreen()

        app.exec()
