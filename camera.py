import os
import sys

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

# QApplication must be the very first Qt object created — before any import
# that touches picamera2's Qt previews, qtawesome, or any QWidget/QColor/QFont.
_app = QApplication(sys.argv)

# ---------------------------------------------------------------------------

from functions import Echo, Console
from controls.remote import Remote
from controls.touchscreen import Touchscreen
import globals

version = '2024.02.24'

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

# Camera configure + start is deferred to CameraWindow.__init__ so that
# QPicamera2 registers its frame callback before frames start arriving.
touchscreen = Touchscreen()
remote = Remote()
