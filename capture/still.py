from functions import Console
from globals import Cameras
from capture.postProcess import PostProcess

console = Console()
postProcess = PostProcess()

# ------------------------------------------------------------------------------

class Still:
	@staticmethod
	def capture(camera: str, filePath: str, rotate: int, raw: bool = True):

		cameraList = Cameras()
		if camera == 'secondary':
			module = cameraList.Secondary.module
			exifData = cameraList.Secondary.exif
			stillConfiguration = cameraList.Secondary.stillConfiguration
		else:
			module = Cameras().Primary.module
			exifData = cameraList.Primary.exif
			stillConfiguration = cameraList.Primary.stillConfiguration

		request = module.switch_mode_and_capture_request(stillConfiguration)
		request.save('main', filePath)
		
		postProcess.postProcessImage(filePath, rotate, exifData)
					
		if raw == True:
			request.save_dng(filePath.replace('.jpg', '.dng'))

		request.release()
