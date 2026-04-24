from functions import Console
from capture.still import Still
from capture.video import Video
from file import File
from PySide6.QtCore import Slot
import globals
import threading

# libcamera control enum values (integers).  picamera2 requires int, not str.
_METERING = {'CentreWeighted': 0, 'Spot': 1, 'Matrix': 2}
_EXPOSURE  = {'Normal': 0, 'Short': 1, 'Long': 2}
_AWB       = {'Auto': 0, 'Incandescent': 1, 'Tungsten': 2,
              'Fluorescent': 3, 'Indoor': 4, 'Daylight': 5, 'Cloudy': 6}

console = Console()

class Actions:

# ------------------------------------------------------------------------------

	@Slot()
	def CaptureImage(self):
		capturePrimaryThread = threading.Thread(
			target=Still.capture,
			args=('primary', File.GetPath(True, False, 1), globals.primary.rotation, globals.primary.raw)
		)
		capturePrimaryThread.start()
		if globals.state.stereoCaptureEnabled and globals.secondary is not None:
			captureSecondaryThread = threading.Thread(
				target=Still.capture,
				args=('secondary', File.GetPath(True, False, 2), globals.secondary.rotation, globals.secondary.raw)
			)
			captureSecondaryThread.start()


# ------------------------------------------------------------------------------

	@Slot()
	def CaptureVideo(self):
		capturePrimaryThread = threading.Thread(
			target=Video.capture,
			args=('primary', File.GetPath(True, True, 1), globals.primary.rotation)
		)
		capturePrimaryThread.start()
		if globals.state.stereoCaptureEnabled and globals.secondary is not None:
			captureSecondaryThread = threading.Thread(
				target=Video.capture,
				args=('secondary', File.GetPath(True, True, 2), globals.secondary.rotation)
			)
			captureSecondaryThread.start()

# ------------------------------------------------------------------------------

	@Slot()
	def SetStereo(self):
		if globals.cameras.count > 1 and globals.secondary is not None:
			globals.state.stereoCaptureEnabled = not globals.state.stereoCaptureEnabled
		else:
			globals.state.stereoCaptureEnabled = False


# ------------------------------------------------------------------------------

	@Slot()
	def SetShutter(self, direction: str):
		shutter = globals.state.shutter
		shutterShort: int = globals.state.shutterShort
		shutterLong: int = globals.state.shutterLong
		shutterLongThreshold: int = globals.state.shutterLongThreshold
		defaultFramerate: int = globals.state.defaultFramerate

		if direction == 'up':
			# Faster shutter = shorter exposure = smaller number
			if shutter == 0:
				shutter = shutterLong
			elif shutter > shutterShort:
				shutter = max(shutterShort, int(shutter / 1.5))
		else:
			# Slower shutter = longer exposure = larger number
			if shutter == 0:
				shutter = shutterShort
			elif shutter < shutterLong:
				shutter = min(shutterLong, int(shutter * 1.5))
			elif shutter >= shutterLong:
				shutter = 0  # wrap back to auto

		try:
			globals.state.shutter = shutter

			# Adjust framerate for long exposure
			if shutter == 0 or shutter <= shutterLongThreshold:
				# Restore normal framerate
				frame_us = int(1_000_000 / defaultFramerate)
				globals.primary.module.set_controls({"FrameDurationLimits": (frame_us, frame_us)})
			else:
				# Slow framerate for long exposure (5fps max)
				min_frame_us = int(shutter * 1.1)
				globals.primary.module.set_controls({"FrameDurationLimits": (min_frame_us, min_frame_us)})

			if shutter == 0:
				globals.primary.module.set_controls({"ExposureTime": 0, "AeEnable": True})
			else:
				globals.primary.module.set_controls({"ExposureTime": shutter, "AeEnable": False})

		except Exception as ex:
			globals.state.lastMessage = 'Invalid Shutter Speed! ' + str(shutter)
			console.warn(globals.state.lastMessage + str(ex))


# ------------------------------------------------------------------------------

	@Slot()
	def SetISO(self, direction: str):
		iso: int = globals.state.iso
		isoMin: int = globals.state.isoMin
		isoMax: int = globals.state.isoMax

		if direction == 'up':
			if iso == 0:
				iso = isoMin
			elif iso < isoMax:
				iso = min(isoMax, int(iso * 2))
		else:
			if iso == 0:
				iso = isoMax
			elif iso > isoMin:
				iso = max(isoMin, int(iso / 2))
			elif iso == isoMin:
				iso = 0  # back to auto

		try:
			globals.state.iso = iso
			if iso == 0:
				globals.primary.module.set_controls({"AeEnable": True, "AnalogueGain": 0.0})
			else:
				globals.primary.module.set_controls({"AeEnable": False, "AnalogueGain": iso / 100.0})
		except Exception as ex:
			globals.state.lastMessage = 'Invalid ISO! ' + str(iso)
			console.warn(globals.state.lastMessage + str(ex))


# ------------------------------------------------------------------------------

	@Slot()
	def SetExposureMode(self):
		exposureMode: str = globals.state.exposureMode
		modes = ['Normal', 'Short', 'Long', 'Disabled']
		idx = modes.index(exposureMode) if exposureMode in modes else 0
		exposureMode = modes[(idx + 1) % len(modes)]

		try:
			globals.state.exposureMode = exposureMode
			if exposureMode == 'Disabled':
				globals.primary.module.set_controls({"AeEnable": False})
			else:
				globals.primary.module.set_controls({
					"AeEnable": True,
					"AeExposureMode": _EXPOSURE.get(exposureMode, 0),
				})
		except Exception as ex:
			globals.state.lastMessage = 'Invalid Exposure Mode! ' + str(exposureMode)
			console.warn(globals.state.lastMessage + str(ex))


# ------------------------------------------------------------------------------

	@Slot()
	def SetMeteringMode(self):
		meteringMode: str = globals.state.meteringMode
		modes = ['CentreWeighted', 'Spot', 'Matrix']
		idx = modes.index(meteringMode) if meteringMode in modes else 0
		meteringMode = modes[(idx + 1) % len(modes)]

		try:
			globals.state.meteringMode = meteringMode
			globals.primary.module.set_controls({
				"AeMeteringMode": _METERING.get(meteringMode, 0),
			})
		except Exception as ex:
			globals.state.lastMessage = 'Invalid Metering Mode! ' + str(meteringMode)
			console.warn(globals.state.lastMessage + str(ex))


# ------------------------------------------------------------------------------

	@Slot()
	def SetExposureValue(self, direction: str):
		exposureValue: int = globals.state.exposureValue
		exposureValueMin: int = globals.state.exposureValueMin
		exposureValueMax: int = globals.state.exposureValueMax

		if direction == 'up':
			if exposureValue < exposureValueMax:
				exposureValue += 1
		else:
			if exposureValue > exposureValueMin:
				exposureValue -= 1

		if exposureValue > 0:
			globals.state.exposureValuePrefix = '+'
		elif exposureValue < 0:
			globals.state.exposureValuePrefix = '-'
		else:
			globals.state.exposureValuePrefix = '+/-'

		try:
			globals.state.exposureValue = exposureValue
			globals.primary.module.set_controls({"ExposureValue": float(exposureValue)})
		except Exception as ex:
			globals.state.lastMessage = 'Invalid EV! ' + str(exposureValue)
			console.warn(globals.state.lastMessage + str(ex))


# ------------------------------------------------------------------------------

	@Slot()
	def SetBracket(self, direction: str):
		bracket: int = globals.state.bracket
		exposureValueMin: int = globals.state.exposureValueMin
		exposureValueMax: int = globals.state.exposureValueMax

		if direction == 'up':
			if bracket < exposureValueMax:
				bracket += 1
		else:
			if bracket > 0:
				bracket -= 1

		try:
			globals.state.bracket = bracket
			base_ev = globals.state.exposureValue
			globals.state.bracketLow = max(exposureValueMin, base_ev - bracket)
			globals.state.bracketHigh = min(exposureValueMax, base_ev + bracket)
		except Exception as ex:
			globals.state.lastMessage = 'Invalid Bracket! ' + str(bracket)
			console.warn(globals.state.lastMessage + str(ex))


# ------------------------------------------------------------------------------

	@Slot()
	def SetAWBMode(self):
		awbMode: str = globals.state.awbMode
		modes = ['Auto', 'Tungsten', 'Fluorescent', 'Indoor', 'Daylight', 'Cloudy', 'Disabled']
		idx = modes.index(awbMode) if awbMode in modes else 0
		awbMode = modes[(idx + 1) % len(modes)]

		try:
			globals.state.awbMode = awbMode
			if awbMode == 'Disabled':
				globals.primary.module.set_controls({"AwbEnable": False})
			else:
				globals.primary.module.set_controls({
					"AwbEnable": True,
					"AwbMode": _AWB.get(awbMode, 0),
				})
		except Exception as ex:
			globals.state.lastMessage = 'Invalid AWB Mode! ' + str(awbMode)
			console.warn(globals.state.lastMessage + str(ex))


# ------------------------------------------------------------------------------

	@Slot()
	def SetTimer(self):
		timer: int = globals.state.timer
		sequence = [0, 3, 5, 10]
		idx = sequence.index(timer) if timer in sequence else 0
		globals.state.timer = sequence[(idx + 1) % len(sequence)]


# ------------------------------------------------------------------------------

	@Slot()
	def ToggleSettings(self):
		# Handled directly by the UI layer
		pass


# ------------------------------------------------------------------------------

	@Slot()
	def SetLights(self, red: int = 0, green: int = 0, blue: int = 0, white: int = 0):
		globals.state.lights.red = red
		globals.state.lights.green = green
		globals.state.lights.blue = blue
		globals.state.lights.white = white


# ------------------------------------------------------------------------------
