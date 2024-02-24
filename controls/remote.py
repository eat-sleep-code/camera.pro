from functions import Console
from actions import Actions
import evdev
from evdev import ecodes as e

console = Console()
actions = Actions()

class Remote:
	device = evdev.InputDevice('/dev/input/event1')
	console.debug(device)

	try:
		for event in device.read_loop():
			if event.type == evdev.ecodes.EV_KEY:
				if event.value == 1:  # Short Press
					actions.CaptureImage()
				elif event.value == 2:  # Long Press
					actions.CaptureVideo()
				elif event.value == 0:  # Release
					pass
	except KeyboardInterrupt:
		pass