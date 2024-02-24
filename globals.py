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
		with open('../config.json') as configFile:
			self.configData = json.load(configFile)[0]
	
	def __call__(self):
		return self.configData
	

# ==============================================================================
	

class Primary:
	def __init__(self):
		config = Config()
		self.module = Picamera2(0)
		self.controls = Controls(self.module)
		
		
		self.stillConfiguration  = self.module.create_still_configuration(main={"size": self.module.sensor_resolution}, colour_space = ColorSpace.Sycc())
		self.videoConfiguration = self.module.create_video_configuration(main={"size": (1920, 1080)}, colour_space = ColorSpace.Rec709())
		self.rotation = config['cameras']['primary']['rotation'] or 0
		self.raw = config['cameras']['primary']['raw'] or True
		primaryExif = EXIF()
		primaryExif.fStop = config['cameras']['primary']['exif']['fstop']
		primaryExif.focalLength = config['cameras']['primary']['exif']['focalLength']
		primaryExif.focalLengthEquivalent = config['cameras']['primary']['exif']['focalLengthEquivalent']	
		self.exif: EXIF = primaryExif
		self.isRecording: bool = False

# --------------------------------------------------------------------------
				
class Secondary:
	def __init__(self):
		if Cameras.count > 1:
			config = Config()
			self.module = Picamera2(1)
			self.controls = Controls(self.module)
			
			self.stillConfiguration  = self.module.create_still_configuration(main={"size": self.module.sensor_resolution}, colour_space = ColorSpace.Sycc())
			self.videoConfiguration = self.module.create_video_configuration(main={"size": (1920, 1080)}, colour_space = ColorSpace.Rec709())
			self.rotation = config['cameras']['secondary']['rotation'] or 0
			self.raw = config['cameras']['secondary']['rotation'] or True
			secondaryExif = EXIF()
			secondaryExif.fStop = config['cameras']['secondary']['exif']['fstop']
			secondaryExif.focalLength = config['cameras']['secondary']['exif']['focalLength']
			secondaryExif.focalLengthEquivalent = config['cameras']['secondary']['exif']['focalLengthEquivalent']	
			self.exif: EXIF = secondaryExif
			self.isRecording: bool = False

# --------------------------------------------------------------------------
			
class Cameras:
	def __init__(self):
		self.count: int = len(Picamera2.global_camera_info()) or 0
		self.Primary = Primary()
		self.Secondary = Secondary()


# ==============================================================================


class Preview:
	def __init__(self):
		config = Config()
		self.width: int = int(config['display']['width']) or 800
		self.height: int = int(config['display']['height']) or 600
		self.active: bool = False


# ==============================================================================


class State:
	def __init__(self):
		
		self.lastMessage: str = ''
		self.imageCount: int = 0
		
		# ----------------------------------------------------------------------
		
		self.stereoCaptureEnabled: bool = False

		# ----------------------------------------------------------------------

		self.shutter = 'auto'
		self.shutterLong: int = 30000
		self.shutterLongThreshold: int = 1000
		self.shutterShort: int = 0
		self.defaultFramerate: int = 30

		# ----------------------------------------------------------------------		

		self.iso = 'auto'
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
		
		self.awbMode: str = 'auto'

		# ----------------------------------------------------------------------

		self.timer: int = 0

		# ----------------------------------------------------------------------

		self.detections = []


# ==============================================================================


def initialize():
	global config
	config = Config()

	global cameras 
	cameras = Cameras()

	global primaryCamera
	primaryCamera = Cameras().Primary()

	global preview
	preview = Preview()

	global state
	state = State()


def restart():
	os.execv(sys.executable, ['python'] + sys.argv)