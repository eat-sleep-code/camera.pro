from functions import Console
from capture.postProcess import PostProcess
from libcamera import ColorSpace
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

		# Patch module.camera_config (the live preview config picamera2 will
		# switch back to after the still) so it has all keys that
		# check_camera_config() requires.  Older/newer picamera2 versions may
		# strip 'raw' and/or 'colour_space' from the dict during configure().
		if hasattr(module, 'camera_config') and isinstance(module.camera_config, dict):
			module.camera_config.setdefault('raw', None)
			module.camera_config.setdefault('colour_space', ColorSpace.Sycc())

		request = module.switch_mode_and_capture_request(stillConfiguration)
		request.save('main', filePath)

		postProcess.postProcessImage(filePath, rotate, exifData)

		if raw:
			request.save_dng(filePath.replace('.jpg', '.dng'))

		request.release()

		console.info('Capture complete: ' + filePath)
