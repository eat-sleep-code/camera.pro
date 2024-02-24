from functions import Console
from capture.postProcess import PostProcess
import globals

console = Console()
postProcess = PostProcess()

# ------------------------------------------------------------------------------

class Still:
	@staticmethod
	def capture(camera: str, filePath: str, rotate: int, raw: bool = True):

	
		if camera == 'secondary':
			module = globals.Secondary.module
			exifData = globals.Secondary.exif
			stillConfiguration = globals.Secondary.stillConfiguration
		else:
			module = globals.Cameras().Primary.module
			exifData = globals.Primary.exif
			stillConfiguration = globals.Primary.stillConfiguration

		request = module.switch_mode_and_capture_request(stillConfiguration)
		request.save('main', filePath)
		
		postProcess.postProcessImage(filePath, rotate, exifData)
					
		if raw == True:
			request.save_dng(filePath.replace('.jpg', '.dng'))

		request.release()
