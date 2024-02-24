from functions import Console
from globals import Cameras, Primary, Secondary, State
from capture.still import Still
from file import File
from PySide6.QtCore import Slot
import fractions
import threading

console = Console()

class Actions:

# ------------------------------------------------------------------------------				

	@Slot()
	def CaptureImage(self):
		stereoCaptureEnabled: bool = State.stereoCaptureEnabled
		capturePrimaryThread = threading.Thread(target=Still().capture('primary', File.GetPath(True, False, 1), Primary.rotation, Primary.raw))
		capturePrimaryThread.start()
		Still()
		if stereoCaptureEnabled == True:
			captureSecondaryThread = threading.Thread(target=Still().capture('secondary', File.GetPath(True, False, 2), Secondary.rotation, Secondary.raw))
			captureSecondaryThread.start()

	
# ------------------------------------------------------------------------------				

	@Slot()
	def CaptureVideo(self):
		pass

# ------------------------------------------------------------------------------				


	@Slot()
	def SetStereo(self):
		stereoCaptureEnabled: bool = State.stereoCaptureEnabled
		if Cameras.count > 1:
			if stereoCaptureEnabled == False:
				#TODO: // Start Camera B
				stereoCaptureEnabled = True
			else:
				#TODO: // Stop Camera B
				stereoCaptureEnabled = False
		else:
			stereoCaptureEnabled = False
		State.stereoCaptureEnabled = stereoCaptureEnabled
		

# ------------------------------------------------------------------------------				


	@Slot()
	def SetShutter(self, direction: str):
		shutter = State.shutter
		shutterShort: int = State.shutterShort
		shutterLong: int = State.shutterLong
		shutterLongThreshold: int = State.shutterLongThreshold
		defaultFramerate: int = State.defaultFramerate

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
			State.shutter = shutter
			if Primary.module.framerate == defaultFramerate and shutter > shutterLongThreshold:
				Primary.module.framerate=fractions.Fraction(5, 1000)
			elif Primary.module.framerate != shutterLongThreshold and shutter <= shutterLongThreshold:
				Primary.module.framerate = defaultFramerate
		
			if shutter == 0:
				Primary.controls.ExposureTime = 0
			else:
				Primary.controls.ExposureTime = shutter * 1000
		except Exception as ex:
			State.lastMessage = 'Invalid Shutter Speed! ' + str(shutter)
			console.warn(State.lastMessage + str(ex))
			

# ------------------------------------------------------------------------------				


	@Slot()
	def SetISO(self, direction: str):
		iso: int = State.iso
		isoMin: int = State.isoMin
		isoMax: int = State.isoMax


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
				Primary.controls.AeEnable = 1
				iso = 0
			else: 
				Primary.controls.AeEnable = 0
				iso = int(iso)
				if iso < isoMin:	
					iso = isoMin
				elif iso > isoMax:
					iso = isoMax	
		except Exception as ex:
			State.lastMessage = 'Invalid Auto Exposure Setting! ' + str(iso)
			console.warn(State.lastMessage + str(ex))

		try:	
			State.iso = iso
			analogGain = iso/100
			Primary.controls.AnalogueGain = analogGain
		except Exception as ex:
			State.lastMessage = 'Invalid ISO! ' + str(iso)
			console.warn(State.lastMessage + str(ex))


# ------------------------------------------------------------------------------				


	@Slot()
	def SetExposureMode(self):
		exposureMode: str =  State.exposureMode
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
				Primary.module.AeExposureMode = 'Normal'
				Primary.module.AeEnable = False
			else:
				Primary.module.AeEnable = True
				Primary.module.AeExposureMode = exposureMode
		except Exception as ex: 
			State.lastMessage = 'Invalid Auto Exposure Mode Setting! ' + str(exposureMode)
			console.warn(State.lastMessage + str(ex))


# ------------------------------------------------------------------------------				


	@Slot()
	def SetMeteringMode(self):
		meteringMode: str =  State.meteringMode
		if meteringMode == 'CentreWeighted':
			meteringMode = 'Spot'
		elif meteringMode == 'Spot':
			meteringMode = 'Matrix'
		else:
			meteringMode = 'CentreWeighted'

		try:	
			Primary.module.AeMeteringMode = meteringMode
		except Exception as ex: 
			State.lastMessage = 'Invalid Auto Exposure Metering Mode Setting! ' + str(meteringMode)
			console.warn(State.lastMessage + str(ex))


# ------------------------------------------------------------------------------				


	@Slot()
	def SetExposureValue(self, direction: str):
		exposureValue: int = State.exposureValue
		exposureValueMin: int = State.exposureValueMin
		exposureValueMax: int = State.exposureValueMax

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
			State.exposureValue = exposureValue
			Primary.module.ExposureValue = exposureValue
			State.exposureValuePrefix = exposureValuePrefix
			
		except Exception as ex: 
			State.lastMessage = 'Invalid Exposure Compensation Setting! ' + str(exposureValue)
			console.warn(State.lastMessage + str(ex))
			

# ------------------------------------------------------------------------------				


	@Slot()
	def SetBracket(self, direction: str):    
		bracket: int = State.bracket
		bracketLow: int = State.bracketLow
		bracketHigh: int = State.bracketHigh
		exposureValueMin: int = State.exposureValueMin
		exposureValueMax: int = State.exposureValueMax

		if direction == 'up':
			if bracket < exposureValueMax:	
				bracket = int(bracket + 1)
		else:
			if bracket > 0:					
				bracket = int(bracket - 1)

		try:
			bracketLow = Primary.controls.ExposureValue - bracket
			if bracketLow < exposureValueMin:
				bracketLow = exposureValueMin
			bracketHigh = Primary.controls.ExposureValue + bracket
			if bracketHigh > exposureValueMax:
				bracketHigh = exposureValueMax

			State.bracketLow = bracketLow
			State.bracketHigh = bracketHigh
		
		except Exception as ex:
			State.lastMessage = 'Invalid Exposure Bracketing Value! ' + str(bracket)
			console.warn(State.lastMessage + str(ex))


# ------------------------------------------------------------------------------				


	@Slot()
	def SetAWBMode(self):
		awbMode: str = State.awbMode 
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
				Primary.module.AwbMode = 'Auto'
				Primary.module.AwbEnable = False
			else:
				Primary.module.AwbEnable = True
				Primary.module.AwbMode = exposureMode
		except Exception as ex: 
			State.lastMessage = 'Invalid Auto Exposure Metering Mode Setting! ' + str(exposureMode)
			console.warn(State.lastMessage + str(ex))


# ------------------------------------------------------------------------------	

	@Slot()
	def SetTimer(self):
		timer: int = State.timer 
		if timer == 0:
			timer = 3
		elif timer == 3:
			timer = 5
		elif timer == 5:
			timer = 10
		else:
			timer = 0
		
		State.timer = timer

# ------------------------------------------------------------------------------			


	@Slot()
	def ToggleSettings(self):
		pass


# ------------------------------------------------------------------------------				
