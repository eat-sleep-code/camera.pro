from globals import Config, State
import datetime
import os


class File:
	def GetPath(timestamped: bool = True, isVideo: bool = False):
		config = Config()
		outputDirectory = config['outputDirectory']
		try:
			os.makedirs(outputDirectory, exist_ok = True)
		except OSError:
			console.error(' ERROR: Creation of the output folder ' + outputDirectory + ' failed!')
			echo.on()
			quit()
		else:
			return outputDirectory + File.GetName(timestamped, isVideo)



	def GetName(timestamped: bool = True, isVideo: bool = False):
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
				return datestamp + '-' + timestamp + '-' + str(state.imageCount).zfill(2) + extension
			else:
				return datestamp + '-' + str(state.imageCount).zfill(8) + extension
