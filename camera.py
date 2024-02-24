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
touchscreen = Touchscreen()
remote = Remote()

# ==============================================================================

try:
	globals.Primary.module.set_controls({"AfMode": controls.AfModeEnum.Continuous})
except Exception as ex:
	console.info('Camera 1 does not support autofocus.')
	pass

if globals.Cameras.count > 1:
	try:
		globals.Primary.module.set_controls({"AfMode": controls.AfModeEnum.Continuous})
	except Exception as ex:
		console.info('Camera 2 does not support autofocus.')
		pass
