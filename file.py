from functions import Console, Echo
from globals import Config, State
import datetime
import os

console = Console()
echo = Echo()

class File:

	def GetPath(timestamped: bool = True, isVideo: bool = False, subIdentifier: int = 1):
		config = Config()
		now = datetime.datetime.now()
		datestamp = now.strftime('%Y%m%d')
		outputDirectory = config['outputDirectory']
		try:
			os.makedirs(outputDirectory, exist_ok = True)
			try:
				os.makedirs(outputDirectory + datestamp, exist_ok = True)
			except OSError:
				console.error('Creation of the output folder ' + outputDirectory + datestamp + ' failed!')
				echo.on()
				quit()
		except OSError:
			console.error(' ERROR: Creation of the output folder ' + outputDirectory + ' failed!')
			echo.on()
			quit()
		else:
			return outputDirectory + File.GetName(timestamped, isVideo, subIdentifier)


	# --------------------------------------------------------------------------
		

	def GetName(timestamped: bool = True, isVideo: bool = False, subIdentifier: int = 1):
		now = datetime.datetime.now()
		datestamp = now.strftime('%Y%m%d')
		timestamp = now.strftime('%H%M%S')		
				
		if isVideo==True:
			extension = '.h264'
			return datestamp + '-' + timestamp + extension
		else:
			state = State()
			extension = '.jpg'
			if timestamped == True:
				return datestamp + '-' + timestamp + '-' + str(state.imageCount).zfill(2) + '-' + str(subIdentifier).zfill(2) + extension
			else:
				return datestamp + '-' + str(state.imageCount).zfill(8) + extension
