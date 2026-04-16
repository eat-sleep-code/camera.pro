from functions import Console
from capture.postProcess import PostProcess
import globals

console = Console()
postProcess = PostProcess()

# ------------------------------------------------------------------------------

class Still:
	@staticmethod
	def capture(camera: str, filePath: str, rotate: int, raw: bool = True):

		if camera == 'secondary' and globals.secondary is not None:
			module = globals.secondary.module
			exifData = globals.secondary.exif
			stillConfiguration = globals.secondary.stillConfiguration
			previewConfiguration = globals.secondary.previewConfiguration
		else:
			module = globals.primary.module
			exifData = globals.primary.exif
			stillConfiguration = globals.primary.stillConfiguration
			previewConfiguration = globals.primary.previewConfiguration

		console.info('Capturing image: ' + filePath)

		request = module.switch_mode_and_capture_request(stillConfiguration)
		request.save('main', filePath)

		postProcess.postProcessImage(filePath, rotate, exifData)

		if raw:
			request.save_dng(filePath.replace('.jpg', '.dng'))

		request.release()

		console.info('Capture complete: ' + filePath)
