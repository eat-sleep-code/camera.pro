from functions import Console, Echo
from globals import Config, State
import datetime
import os
import pwd

console = Console()
echo = Echo()

class File:

	def GetPath(timestamped: bool = True, isVideo: bool = False, subIdentifier: int = 1):
		config = Config()
		now = datetime.datetime.now()
		datestamp = now.strftime('%Y%m%d')
		sudo_user = os.environ.get('SUDO_USER')
		if sudo_user:
			home = pwd.getpwnam(sudo_user).pw_dir
			outputDirectory = config['outputDirectory'].replace('~', home, 1)
		else:
			outputDirectory = os.path.expanduser(config['outputDirectory'])
		if not outputDirectory.endswith(os.sep):
			outputDirectory += os.sep
		try:
			os.makedirs(outputDirectory, exist_ok = True)
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
