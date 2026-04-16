from functions import Console
from picamera2.encoders import H264Encoder, Quality
import globals

console = Console()

# ------------------------------------------------------------------------------

class Video:
	@staticmethod
	def capture(camera: str, filePath: str, rotate: int):

		if camera == 'secondary' and globals.secondary is not None:
			module = globals.secondary.module
			videoConfiguration = globals.secondary.videoConfiguration
			previewConfiguration = globals.secondary.previewConfiguration
			isRecording: bool = globals.secondary.isRecording
		else:
			module = globals.primary.module
			videoConfiguration = globals.primary.videoConfiguration
			previewConfiguration = globals.primary.previewConfiguration
			isRecording: bool = globals.primary.isRecording

		if not isRecording:
			console.info('Capturing video: ' + filePath)
			module.stop()
			module.configure(videoConfiguration)
			encoder = H264Encoder()
			module.start_recording(encoder, filePath, quality=Quality.VERY_HIGH)
			if camera == 'secondary' and globals.secondary is not None:
				globals.secondary.isRecording = True
			else:
				globals.primary.isRecording = True
		else:
			module.stop_recording()
			if camera == 'secondary' and globals.secondary is not None:
				globals.secondary.isRecording = False
			else:
				globals.primary.isRecording = False
			console.info('Video capture complete.')
			# Restart preview
			module.configure(previewConfiguration)
			module.start()
