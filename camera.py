import os
import sys
import signal
import threading

# ---------------------------------------------------------------------------
# Qt platform plugin — must be set before any Qt import.
#
# On Pi OS Lite (no X11 / Wayland desktop), Qt's xcb plugin can't connect
# to a display server and eglfs_kms fails on the Pi 5 GPU stack.
# 'linuxfb' drives the framebuffer directly and works reliably on Pi OS Lite.
# Users can override by setting QT_QPA_PLATFORM in the environment beforehand.
if 'QT_QPA_PLATFORM' not in os.environ:
    os.environ['QT_QPA_PLATFORM'] = 'linuxfb'

# Enable evdev touch input on linuxfb (no desktop display server to handle it).
# Qt will auto-detect the touch device; override QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS
# in the environment if you need to pin a specific device path, e.g.:
#   export QT_QPA_EVDEV_TOUCHSCREEN_PARAMETERS=/dev/input/event0
os.environ.setdefault('QT_QPA_GENERIC_PLUGINS', 'evdevtouch')

# Also suppress noisy libcamera log output.
os.environ.setdefault('LIBCAMERA_LOG_LEVELS', '3')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# QApplication must be the very first Qt object created — before any import
# that touches picamera2's Qt previews, qtawesome, or any QWidget/QColor/QFont.
_app = QApplication(sys.argv)

# ---------------------------------------------------------------------------
# Signal handling
#
# Qt's C++ event loop blocks Python's bytecode evaluator, so SIGINT (Ctrl+C)
# is received by the OS but KeyboardInterrupt is never raised — the signal
# just disappears.  Fix: a 200 ms null-timer lets Python regain the GIL
# briefly every tick so it can dispatch any pending signals.

_signal_timer = QTimer()
_signal_timer.start(200)
_signal_timer.timeout.connect(lambda: None)

def _request_quit(signum=None, frame=None):
    """Ask Qt to exit its event loop cleanly."""
    _app.quit()

signal.signal(signal.SIGINT,  _request_quit)
signal.signal(signal.SIGTERM, _request_quit)

# ---------------------------------------------------------------------------

from functions import Echo, Console
from controls.remote import Remote
from controls.touchscreen import Touchscreen
import globals

version = '2026.04.24'

# ---------------------------------------------------------------------------

globals.initialize()
console = Console()
echo = Echo()

# Detect autofocus capability by inspecting available controls.
# Works before the camera is started — no set_controls() needed here.
if 'AfMode' in globals.primary.module.camera_controls:
    globals.primary.hasAutofocus = True
    console.info('Camera 1 supports autofocus.')
else:
    console.info('Camera 1 does not support autofocus.')

if globals.cameras.count > 1 and globals.secondary is not None:
    if 'AfMode' in globals.secondary.module.camera_controls:
        globals.secondary.hasAutofocus = True
        console.info('Camera 2 supports autofocus.')
    else:
        console.info('Camera 2 does not support autofocus.')

# ---------------------------------------------------------------------------
# Cleanup — runs when QApplication.quit() is called (before event loop exits).

def _on_quit():
    """Stop camera hardware so it doesn't hold resources after exit."""
    for unit_name in ('primary', 'secondary'):
        unit = getattr(globals, unit_name, None)
        if unit is None:
            continue
        try:
            if unit.isRecording:
                unit.module.stop_recording()
            unit.module.stop()
        except Exception:
            pass

_app.aboutToQuit.connect(_on_quit)

# ---------------------------------------------------------------------------
# Remote control runs in a daemon thread so it is killed automatically when
# the main thread exits.  If it ran after Touchscreen() it would block forever
# because Remote.__init__ contains an evdev read_loop().
threading.Thread(target=Remote, daemon=True, name='remote').start()

# Camera configure + start is deferred to CameraWindow.__init__ so that
# QPicamera2 registers its frame callback before frames start arriving.
# This call blocks until QApplication.quit() is invoked (e.g. Ctrl+C).
touchscreen = Touchscreen()

# ---------------------------------------------------------------------------
# Post-exit framebuffer blank
#
# linuxfb leaves the last rendered frame painted on the display after the
# process exits — the image just sits there, frozen.  Writing zeros to
# /dev/fb0 blanks the screen so it doesn't look like the app is still running.

try:
    with open('/dev/fb0', 'wb') as _fb:
        _fb.write(b'\x00' * (800 * 480 * 4))
except Exception:
    pass
