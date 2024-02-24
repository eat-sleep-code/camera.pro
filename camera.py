from libcamera import controls
from functions import Echo, Console
from globals import Cameras
from controls.touchscreen import Touchscreen


version = '2024.02.23'


console = Console()
echo = Echo()
touchscreen = Touchscreen()

try:
	Cameras.Primary.module.set_controls({"AfMode": controls.AfModeEnum.Continuous})
except Exception as ex:
	console.info('Camera 1 does not support autofocus.')
	pass

if Cameras.count > 1:
	try:
		Cameras.Secondary.module.set_controls({"AfMode": controls.AfModeEnum.Continuous})
	except Exception as ex:
		console.info('Camera 2 does not support autofocus.')
		pass
