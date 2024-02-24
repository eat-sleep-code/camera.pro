from functions import Console
from picamera2.encoders import H264Encoder, Quality
import globals

console = Console()

# ------------------------------------------------------------------------------

class Video:
	@staticmethod
	def capture(camera: str, filePath: str, rotate: int):

		if camera == 'secondary':
			module =  globals.Secondary.module
			videoConfiguration = globals.Secondary.videoConfiguration
			isRecording: bool = globals.Secondary.isRecording
		else:
			module = globals.Primary.module
			videoConfiguration = globals.Primary.videoConfiguration


		if isRecording == False:
			module.stop()
			if camera == 'secondary':
				globals.Secondary.isRecording = True
			else:
				globals.Primary.isRecording = True
			filePath = filePath
			module.resolution = (1920, 1080)
			console.info('Capturing video: ' + filePath + '\n')
			module.configure(videoConfiguration)
			encoder = H264Encoder()
			module.start_recording(encoder, filePath, quality=Quality.VERY_HIGH)

		else:
			
			module.stop_recording()
			if camera == 'secondary':
				globals.Secondary.isRecording = False
			else:
				globals.Primary.isRecording = False
			console.info('Capture complete \n')
			camera.start()

