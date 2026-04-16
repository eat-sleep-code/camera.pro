from libcamera import controls
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
# Detect autofocus capability on each camera

try:
	globals.primary.module.set_controls({"AfMode": controls.AfModeEnum.Continuous})
	globals.primary.hasAutofocus = True
except Exception:
	console.info('Camera 1 does not support autofocus.')

if globals.cameras.count > 1 and globals.secondary is not None:
	try:
		globals.secondary.module.set_controls({"AfMode": controls.AfModeEnum.Continuous})
		globals.secondary.hasAutofocus = True
	except Exception:
		console.info('Camera 2 does not support autofocus.')

# ==============================================================================
# Start camera preview and launch UI

globals.primary.module.configure(globals.primary.previewConfiguration)
globals.primary.module.start()

touchscreen = Touchscreen()
remote = Remote()
