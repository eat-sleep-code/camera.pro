from capture.postProcess import EXIF
from libcamera import ColorSpace
from picamera2 import Picamera2
from picamera2.controls import Controls
import json
import os
import sys



# ==============================================================================

class Config:
	def __init__(self):
		try:
			with open('/home/pi/camera.pro/config.json') as configFile:
				self.configData = json.load(configFile)[0]
		except FileNotFoundError:
			raise RuntimeError("Configuration file not found")
		except json.JSONDecodeError:
			raise RuntimeError("Configuration file is malformed")

	def __call__(self):
		return self.configData

	def __getitem__(self, key):
		if key not in self.configData:
			raise KeyError(f"Key '{key}' not found in configuration")
		return self.configData[key]


# ==============================================================================


class CameraUnit:
	"""Represents a single camera (primary or secondary)."""
	def __init__(self, index: int, config_key: str):
		config = Config()
		self.module = Picamera2(index)
		self.controls = Controls(self.module)

		self.previewConfiguration = self.module.create_preview_configuration(
			main={"size": (800, 600)},
			colour_space=ColorSpace.Sycc()
		)
		self.previewConfiguration.setdefault('raw', None)

		self.stillConfiguration = self.module.create_still_configuration(
			main={"size": self.module.sensor_resolution},
			colour_space=ColorSpace.Sycc()
		)
		self.stillConfiguration.setdefault('raw', None)

		self.videoConfiguration = self.module.create_video_configuration(
			main={"size": (1920, 1080)},
			colour_space=ColorSpace.Rec709()
		)
		self.videoConfiguration.setdefault('raw', None)

		self.rotation: int = config['cameras'][config_key]['rotation'] or 0
		self.raw: bool = config['cameras'][config_key]['raw']

		unit_exif = EXIF()
		unit_exif.fStop = config['cameras'][config_key]['exif']['fStop']
		unit_exif.focalLength = config['cameras'][config_key]['exif']['focalLength']
		unit_exif.focalLengthEquivalent = config['cameras'][config_key]['exif']['focalLengthEquivalent']
		self.exif: EXIF = unit_exif
		self.isRecording: bool = False
		self.hasAutofocus: bool = False


# ==============================================================================

class Cameras:
	count: int = len(Picamera2.global_camera_info()) or 0

	def __init__(self):
		self.Primary = CameraUnit(0, 'primary')
		self.Secondary = CameraUnit(1, 'secondary') if Cameras.count > 1 else None


# ==============================================================================


class Preview:
	def __init__(self):
		config = Config()
		self.width: int = int(config['display']['width']) or 800
		self.height: int = int(config['display']['height']) or 600
		self.active: bool = False

# ==============================================================================

class Lights:
	def __init__(self):
		self.red: int = 0
		self.green: int = 0
		self.blue: int = 0
		self.white: int = 0

# ==============================================================================


class State:
	def __init__(self):

		self.lastMessage: str = ''
		self.imageCount: int = 0

		# ----------------------------------------------------------------------

		self.stereoCaptureEnabled: bool = False

		# ----------------------------------------------------------------------

		# Shutter: 0 = auto, otherwise microseconds
		self.shutter: int = 0
		self.shutterLong: int = 30000
		self.shutterLongThreshold: int = 1000
		self.shutterShort: int = 100
		self.defaultFramerate: int = 30

		# ----------------------------------------------------------------------

		# ISO: 0 = auto, otherwise e.g. 100, 200, 400...
		self.iso: int = 0
		self.isoMin: int = 100
		self.isoMax: int = 1600

		# ----------------------------------------------------------------------

		self.exposureMode: str = 'Normal'

		# ----------------------------------------------------------------------

		self.meteringMode: str = 'CentreWeighted'

		# ----------------------------------------------------------------------

		self.exposureValue: int = 0
		self.exposureValueMin: int = -25
		self.exposureValueMax: int = 25
		self.exposureValuePrefix: str = '+/-'

		# ----------------------------------------------------------------------

		self.bracket: int = 0
		self.bracketLow: int = 0
		self.bracketHigh: int = 0

		# ----------------------------------------------------------------------

		self.awbMode: str = 'Auto'

		# ----------------------------------------------------------------------

		self.timer: int = 0

		# ----------------------------------------------------------------------

		self.lights = Lights()

		# ----------------------------------------------------------------------

		self.detections = []

		# ----------------------------------------------------------------------

		# capture mode: 'photo' or 'video'
		self.captureMode: str = 'photo'

		# exposure mode: 'auto' (P) or 'manual'
		self.programMode: str = 'auto'


# ==============================================================================


def initialize():
	global config, cameras, primary, secondary, preview, state

	config = Config()
	cameras = Cameras()
	primary = cameras.Primary
	secondary = cameras.Secondary   # may be None if single-camera
	preview = Preview()
	state = State()


def restart():
	os.execv(sys.executable, ['python'] + sys.argv)
