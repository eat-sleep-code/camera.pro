from functions import Console
from PIL import Image
import piexif

console = Console()

class EXIF:
	def __init__(self, orientation: int = 1, fStop: float = None, focalLength: float = None, focalLengthEquivalent: float = None):
		self.orientation: int = orientation
		self.fStop: float = fStop
		self.focalLength: float = focalLength
		self.focalLengthEquivalent: float = focalLengthEquivalent




class PostProcess:

	def postProcessImage(self, filePath: str, angle: int, exifData: EXIF):

		try:
			image = Image.open(filePath)
			FileEXIFData = piexif.load(filePath)

			if angle > 0:
				newOrientation = 1
				if angle == 90:
					newOrientation = 6
					image = image.rotate(-90, expand=True)
				elif angle == 180:
					newOrientation = 3
					image = image.rotate(180, expand=True)
				elif angle == 270:
					newOrientation = 8
					image = image.rotate(90, expand=True)
				exifData.orientation = newOrientation
					
				FileEXIFData['Orientation'] = exifData.orientation

			try:
				if exifData.fStop != 0:
					FileEXIFData['Exif'][piexif.ExifIFD.FNumber] = (int(exifData.fStop * 100), 100)
					
				if exifData.focalLength != 0:
					FileEXIFData['Exif'][piexif.ExifIFD.FocalLength] = (int(exifData.focalLength * 100), 100)
					
				if exifData.focalLengthEquivalent != 0:
					FileEXIFData['Exif'][piexif.ExifIFD.FocalLengthIn35mmFilm] = int(exifData.focalLengthEquivalent)
			except Exception as ex:
				console.warn('Could not rotate apply additional EXIF data to image.   Please check supplied data. ' + str(ex))
				pass

			EXIFBytes = piexif.dump(FileEXIFData)
			image.save(filePath, exif=EXIFBytes)
		except Exception as ex:
			console.warn('Could not rotate ' + filePath + ' ' + str(angle) + ' degrees. ' + str(ex))
			pass


#def convertBayerDataToDNG(filePath):
#	try:
#		dng.convert(filePath)
#	except:
#		pass