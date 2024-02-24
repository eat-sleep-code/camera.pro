from PySide6.QtWidgets import QApplication, QVBoxLayout, QPushButton, QWidget
from picamera2.previews.qt import QGlPicamera2
from actions import Actions
import globals
import sys

actions = Actions()



class Touchscreen:
	def __init__(self):
		global app
		app = QApplication(sys.argv)
  
		with open("../ui/style.qss", "r") as styleSheetFile:
			styleSheet = styleSheet.read()
			app.setStyleSheet(styleSheet)

		

		buttonCount: int = 16
		buttonsPerSide: int = int(buttonCount / 2)
		buttonSpacing: int = 10
		screen = QApplication.primaryScreen()
		screenResolution = screen.size()
		screenWidth: int = int(screenResolution.width)
		screenHeight: int = int(screenResolution.height)

		buttonHeight: int = screenHeight / buttonsPerSide - buttonSpacing
		buttonWidth: int = buttonHeight

		# ------------------------------------------------------------------------------		

		appLayerLayout = QVBoxLayout(self)
		self.setLayout(appLayerLayout)

		previewLayer = QWidget(self)
		previewLayerLayout = QVBoxLayout(previewLayer)
		previewLayer.setLayout(previewLayer)

		buttons01Layer = QWidget(self)
		buttons01LayerLayout = QVBoxLayout(buttons01Layer)
		buttons01Layer.setLayout(buttons01LayerLayout)

		buttons02Layer = QWidget(self)
		buttons02LayerLayout = QVBoxLayout(buttons01Layer)
		buttons02Layer.setLayout(buttons01LayerLayout)


		# ------------------------------------------------------------------------------		

		cameraPreview = QGlPicamera2(globals.Primary(), width=screenWidth, height=screenHeight, keep_ar=False)


		# ------------------------------------------------------------------------------		
		
		captureImageButton = QPushButton('Capture Image', buttons01Layer)
		captureImageButton.clicked.connect(actions.CaptureImage)
		captureImageButton.setGeometry(buttonSpacing, 0, buttonWidth, buttonHeight)
		buttons01LayerLayout.addWidget(captureImageButton)
		
		# ------------------------------------------------------------------------------		

		captureVideoButton = QPushButton('Capture Image', buttons01Layer)
		captureVideoButton.clicked.connect(actions.CaptureVideo)
		captureVideoButton.setGeometry((buttonSpacing + buttonHeight) * 2, 0, buttonWidth, buttonHeight)
		buttons01LayerLayout.addWidget(captureVideoButton)
		
		# ------------------------------------------------------------------------------		

		shutterUpButton = QPushButton('Shutter ▲', buttons01Layer)
		shutterUpButton.clicked.connect(actions.SetShutter('up'))
		shutterUpButton.setGeometry((buttonSpacing + buttonHeight) * 3, 0,  buttonWidth, buttonHeight)
		buttons01LayerLayout.addWidget(shutterUpButton)
		
		shutterDownButton = QPushButton('Shutter ▼', buttons01Layer)
		shutterDownButton.clicked.connect(actions.SetShutter('down'))
		shutterDownButton.setGeometry((buttonSpacing + buttonHeight) * 4, 0, buttonWidth, buttonHeight)
		buttons01LayerLayout.addWidget(shutterDownButton)
		
		# ------------------------------------------------------------------------------		

		isoUpButton = QPushButton('ISO ▲', buttons01Layer)
		isoUpButton.clicked.connect(actions.SetISO('up'))
		isoUpButton.setGeometry((buttonSpacing + buttonHeight) * 5, 0, buttonWidth, buttonHeight)
		buttons01LayerLayout.addWidget(isoUpButton)
		
		isoDownButton = QPushButton('ISO ▼', buttons01Layer)
		isoDownButton.clicked.connect(actions.SetISO('down'))
		isoDownButton.setGeometry((buttonSpacing + buttonHeight) * 6, 0, buttonWidth, buttonHeight)
		buttons01LayerLayout.addWidget(isoDownButton)
		
		# ------------------------------------------------------------------------------		

		exposureModeButton = QPushButton('Exposure Mode', buttons01Layer)
		exposureModeButton.clicked.connect(actions.SetExposureMode())
		exposureModeButton.setGeometry((buttonSpacing + buttonHeight) * 7, 0, buttonWidth, buttonHeight)
		buttons01LayerLayout.addWidget(exposureModeButton)
		
		# ------------------------------------------------------------------------------		

		meteringModeButton = QPushButton('Metering Mode', buttons01Layer)
		meteringModeButton.clicked.connect(actions.SetMeteringMode())
		meteringModeButton.setGeometry((buttonSpacing + buttonHeight) * 8, 0, buttonWidth, buttonHeight)
		buttons01LayerLayout.addWidget(meteringModeButton)
		
		# ------------------------------------------------------------------------------	

		evUpButton = QPushButton('EV ▲', buttons02Layer)
		evUpButton.clicked.connect(actions.SetExposureValue('up'))
		evUpButton.setGeometry(buttonSpacing, 0, buttonWidth, buttonHeight)
		buttons02LayerLayout.addWidget(evUpButton)
		
		evDownButton = QPushButton('EV ▼', buttons02Layer)
		evDownButton.clicked.connect(actions.SetExposureValue('down'))
		evDownButton.setGeometry((buttonSpacing + buttonHeight) * 2, 0, buttonWidth, buttonHeight)
		buttons02LayerLayout.addWidget(evDownButton)
		
		# ------------------------------------------------------------------------------		

		bracketUpButton = QPushButton('Bracket ▲', buttons02Layer)
		bracketUpButton.clicked.connect(actions.SetBracket('up'))
		bracketUpButton.setGeometry((buttonSpacing + buttonHeight) * 3, 0, buttonWidth, buttonHeight)
		buttons02LayerLayout.addWidget(bracketUpButton)
		
		bracketDownButton = QPushButton('Bracket ▼', buttons02Layer)
		bracketDownButton.clicked.connect(actions.SetBracket('down'))
		bracketDownButton.setGeometry((buttonSpacing + buttonHeight) * 4, 0, buttonWidth, buttonHeight)
		buttons02LayerLayout.addWidget(bracketDownButton)
		
		# ------------------------------------------------------------------------------		

		awbModeButton = QPushButton('AWB Mode', buttons02Layer)
		awbModeButton.clicked.connect(actions.SetAWBMode())
		awbModeButton.setGeometry((buttonSpacing + buttonHeight) * 5, 0, buttonWidth, buttonHeight)
		buttons02LayerLayout.addWidget(awbModeButton)
		
		# ------------------------------------------------------------------------------		

		timerButton = QPushButton('Timer', buttons02Layer)
		timerButton.clicked.connect(actions.SetTimer())
		timerButton.setGeometry((buttonSpacing + buttonHeight) * 6, 0, buttonWidth, buttonHeight)
		buttons02LayerLayout.addWidget(timerButton)
		
		# ------------------------------------------------------------------------------		

		setStereoButton = QPushButton('Set Stereo', buttons02Layer)
		setStereoButton.clicked.connect(actions.SetStereo)
		setStereoButton.setGeometry((buttonSpacing + buttonHeight) * 7, 0, buttonWidth, buttonHeight)
		if globals.Cameras.count > 1:
			setStereoButton.setEnabled = False
		buttons02LayerLayout.addWidget(setStereoButton)
		
		# ------------------------------------------------------------------------------		

		toggleSettingsButton = QPushButton('Settings', buttons02Layer)
		toggleSettingsButton.clicked.connect(actions.ToggleSettings())
		toggleSettingsButton.setGeometry((buttonSpacing + buttonHeight) * 8, 0, buttonWidth, buttonHeight)
		buttons02LayerLayout.addWidget(toggleSettingsButton)
		
		# ------------------------------------------------------------------------------		

		previewLayer.setGeometry(0, 0, screenWidth, screenHeight)
		buttons01Layer.setGeometry(int(buttonSpacing), 0, buttonWidth, screenHeight)
		buttons02Layer.setGeometry(int(screenWidth - buttonSpacing - buttonWidth), 0, buttonWidth, screenHeight)

		previewLayerLayout.addWidget(cameraPreview)
		appLayerLayout.addWidget(previewLayer)
		appLayerLayout.addWidget(buttons01Layer)
		appLayerLayout.addWidget(buttons02Layer)

		previewLayer.show()
		buttons01Layer.show()
		buttons02Layer.show()
		
		app.exec()