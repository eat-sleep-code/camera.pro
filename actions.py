from functions import Console
from capture.still import Still
from capture.video import Video
from file import File
from PySide6.QtCore import Slot
import globals
import fractions
import threading

console = Console()

class Actions:

# ------------------------------------------------------------------------------				

	@Slot()
	def CaptureImage(self):
		stereoCaptureEnabled: bool = globals.State.stereoCaptureEnabled
		capturePrimaryThread = threading.Thread(target=Still().capture('primary', File.GetPath(True, False, 1), globals.Primary.rotation, globals.Primary.raw))
		capturePrimaryThread.start()
		if stereoCaptureEnabled == True:
			captureSecondaryThread = threading.Thread(target=Still().capture('secondary', File.GetPath(True, False, 2), globals.Secondary.rotation, globals.Secondary.raw))
			captureSecondaryThread.start()

	
# ------------------------------------------------------------------------------				

	@Slot()
	def CaptureVideo(self):
		stereoCaptureEnabled: bool = globals.State.stereoCaptureEnabled
		capturePrimaryThread = threading.Thread(target=Video().capture('primary', File.GetPath(True, False, 1), globals.Primary.rotation))
		capturePrimaryThread.start()
		if stereoCaptureEnabled == True:
			captureSecondaryThread = threading.Thread(target=Video().capture('secondary', File.GetPath(True, False, 2), globals.Secondary.rotation))
			captureSecondaryThread.start()

# ------------------------------------------------------------------------------				


	@Slot()
	def SetStereo(self):
		stereoCaptureEnabled: bool = globals.State.stereoCaptureEnabled
		if globals.Cameras.count > 1:
			if stereoCaptureEnabled == False:
				#TODO: // Start Camera B
				stereoCaptureEnabled = True
			else:
				#TODO: // Stop Camera B
				stereoCaptureEnabled = False
		else:
			stereoCaptureEnabled = False
		globals.State.stereoCaptureEnabled = stereoCaptureEnabled
		

# ------------------------------------------------------------------------------				


	@Slot()
	def SetShutter(self, direction: str):
		shutter = globals.State.shutter
		shutterShort: int = globals.State.shutterShort
		shutterLong: int = globals.State.shutterLong
		shutterLongThreshold: int = globals.State.shutterLongThreshold
		defaultFramerate: int = globals.State.defaultFramerate

		if direction == 'up':
			if shutter == 0:
				shutter = shutterShort
			elif shutter > shutterShort and shutter <= shutterLong:					
				shutter = int(shutter / 1.5)
		else:
			if shutter == 0:						
				shutter = shutterLong
			elif shutter < shutterLong and shutter >= shutterShort:					
				shutter = int(shutter * 1.5)
			elif shutter == shutterShort:
				shutter = 0


		if str(shutter).lower() == 'auto' or str(shutter) == '0':
			shutter = 0
		else:
			shutter = int(float(shutter))
		

		try:
			globals.State.shutter = shutter
			if globals.Primary.module.framerate == defaultFramerate and shutter > shutterLongThreshold:
				globals.Primary.module.framerate=fractions.Fraction(5, 1000)
			elif globals.Primary.module.framerate != shutterLongThreshold and shutter <= shutterLongThreshold:
				globals.Primary.module.framerate = defaultFramerate
		
			if shutter == 0:
				globals.Primary.controls.ExposureTime = 0
			else:
				globals.Primary.controls.ExposureTime = shutter * 1000
		except Exception as ex:
			globals.State.lastMessage = 'Invalid Shutter Speed! ' + str(shutter)
			console.warn(globals.State.lastMessage + str(ex))
			

# ------------------------------------------------------------------------------				


	@Slot()
	def SetISO(self, direction: str):
		iso: int = globals.State.iso
		isoMin: int = globals.State.isoMin
		isoMax: int = globals.State.isoMax


		if direction == 'up':
			if iso == 0:
				iso = isoMin
			elif iso >= isoMin and iso < isoMax:					
				iso = int(iso * 2)
		else:
			if iso == 0:
				iso = isoMax
			elif iso <= isoMax and iso > isoMin:					
				iso = int(iso / 2)
			elif iso == isoMin:
				iso = 0

		try:
			if str(iso).lower() == 'auto' or str(iso) == '0':
				globals.Primary.controls.AeEnable = 1
				iso = 0
			else: 
				globals.Primary.controls.AeEnable = 0
				iso = int(iso)
				if iso < isoMin:	
					iso = isoMin
				elif iso > isoMax:
					iso = isoMax	
		except Exception as ex:
			globals.State.lastMessage = 'Invalid Auto Exposure Setting! ' + str(iso)
			console.warn(globals.State.lastMessage + str(ex))

		try:	
			globals.State.iso = iso
			analogGain = iso/100
			globals.Primary.controls.AnalogueGain = analogGain
		except Exception as ex:
			globals.State.lastMessage = 'Invalid ISO! ' + str(iso)
			console.warn(globals.State.lastMessage + str(ex))


# ------------------------------------------------------------------------------				


	@Slot()
	def SetExposureMode(self):
		exposureMode: str =  globals.State.exposureMode
		if exposureMode == 'Normal':
			exposureMode = 'Short'
		elif exposureMode == 'Short':
			exposureMode = 'Long'
		elif exposureMode == 'Long':
		#	exposureMode = 'Custom'
		#elif exposureMode == 'Custom':
			exposureMode = 'Disabled'
		else:
			exposureMode = 'Normal'

		try:	
			if exposureMode == 'Disabled':
				globals.Primary.module.AeExposureMode = 'Normal'
				globals.Primary.module.AeEnable = False
			else:
				globals.Primary.module.AeEnable = True
				globals.Primary.module.AeExposureMode = exposureMode
		except Exception as ex: 
			globals.State.lastMessage = 'Invalid Auto Exposure Mode Setting! ' + str(exposureMode)
			console.warn(globals.State.lastMessage + str(ex))


# ------------------------------------------------------------------------------				


	@Slot()
	def SetMeteringMode(self):
		meteringMode: str =  globals.State.meteringMode
		if meteringMode == 'CentreWeighted':
			meteringMode = 'Spot'
		elif meteringMode == 'Spot':
			meteringMode = 'Matrix'
		else:
			meteringMode = 'CentreWeighted'

		try:	
			globals.Primary.module.AeMeteringMode = meteringMode
		except Exception as ex: 
			globals.State.lastMessage = 'Invalid Auto Exposure Metering Mode Setting! ' + str(meteringMode)
			console.warn(globals.State.lastMessage + str(ex))


# ------------------------------------------------------------------------------				


	@Slot()
	def SetExposureValue(self, direction: str):
		exposureValue: int = globals.State.exposureValue
		exposureValueMin: int = globals.State.exposureValueMin
		exposureValueMax: int = globals.State.exposureValueMax

		if direction == 'up':
			if exposureValue < exposureValueMax:					
				exposureValue = int(exposureValue + 1)
		else:
			if exposureValue > exposureValueMin:					
				exposureValue = int(exposureValue - 1)
		
		exposureValuePrefix = '+/-'
		if exposureValue > 0:
			exposureValuePrefix = '+'
		elif exposureValue < 0:
			exposureValuePrefix = '-'

		try:
			globals.State.exposureValue = exposureValue
			globals.Primary.module.ExposureValue = exposureValue
			globals.State.exposureValuePrefix = exposureValuePrefix
			
		except Exception as ex: 
			globals.State.lastMessage = 'Invalid Exposure Compensation Setting! ' + str(exposureValue)
			console.warn(globals.State.lastMessage + str(ex))
			

# ------------------------------------------------------------------------------				


	@Slot()
	def SetBracket(self, direction: str):    
		bracket: int = globals.State.bracket
		bracketLow: int = globals.State.bracketLow
		bracketHigh: int = globals.State.bracketHigh
		exposureValueMin: int = globals.State.exposureValueMin
		exposureValueMax: int = globals.State.exposureValueMax

		if direction == 'up':
			if bracket < exposureValueMax:	
				bracket = int(bracket + 1)
		else:
			if bracket > 0:					
				bracket = int(bracket - 1)

		try:
			bracketLow = globals.Primary.controls.ExposureValue - bracket
			if bracketLow < exposureValueMin:
				bracketLow = exposureValueMin
			bracketHigh = globals.Primary.controls.ExposureValue + bracket
			if bracketHigh > exposureValueMax:
				bracketHigh = exposureValueMax

			globals.State.bracketLow = bracketLow
			globals.State.bracketHigh = bracketHigh
		
		except Exception as ex:
			globals.State.lastMessage = 'Invalid Exposure Bracketing Value! ' + str(bracket)
			console.warn(globals.State.lastMessage + str(ex))


# ------------------------------------------------------------------------------				


	@Slot()
	def SetAWBMode(self):
		awbMode: str = globals.State.awbMode 
		if awbMode == 'Auto':
			awbMode = 'Tungsten'
		elif awbMode == 'Tungsten':
			awbMode = 'Fluorescent'
		elif awbMode == 'Fluorescent':
			awbMode = 'Indoor'
		elif awbMode == 'Indoor':
			awbMode = 'Daylight'
		elif awbMode == 'Daylight':
			awbMode = 'Cloudy'
		elif awbMode == 'Cloudy':
		#	awbMode = 'Custom'
		#elif awbMode == 'Custom':
			awbMode = 'Disabled'
		else:
			awbMode = 'Auto'
		try:	
			if awbMode == 'Disabled':
				globals.Primary.module.AwbMode = 'Auto'
				globals.Primary.module.AwbEnable = False
			else:
				globals.Primary.module.AwbEnable = True
				globals.Primary.module.AwbMode = awbMode
		except Exception as ex: 
			globals.State.lastMessage = 'Invalid Auto Exposure Metering Mode Setting! ' + str(awbMode)
			console.warn(globals.State.lastMessage + str(ex))


# ------------------------------------------------------------------------------	


	@Slot()
	def SetTimer(self):
		timer: int = globals.State.timer 
		if timer == 0:
			timer = 3
		elif timer == 3:
			timer = 5
		elif timer == 5:
			timer = 10
		else:
			timer = 0
		
		globals.State.timer = timer


# ------------------------------------------------------------------------------			


	@Slot()
	def ToggleSettings(self):
		pass

				
# ------------------------------------------------------------------------------


	@Slot()
	def SetLights(self, red: int = 0, green: int = 0, blue: int = 0, white: int = 0):
		globals.Lights.red = red
		globals.Lights.green = green
		globals.Lights.blue = blue
		globals.Lights.white = white


# ------------------------------------------------------------------------------
