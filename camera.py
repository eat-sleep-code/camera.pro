from functions import Echo, Console
from controls.remote import Remote
from controls.touchscreen import Touchscreen
import globals

version = '2024.02.24'


# ==============================================================================

globals.initialize()
console = Console()
echo = Echo()

# ==============================================================================
# Detect autofocus capability by inspecting available controls.
# This works before the camera is started — no set_controls() needed here.

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

# ==============================================================================
# Camera configure + start is deferred to CameraWindow.__init__ so that
# QGlPicamera2 is created before picamera2 starts delivering frames.

touchscreen = Touchscreen()
remote = Remote()
