from PySide6.QtWidgets import QApplication, QPushButton
from PySide6.QtCore import Slot
from actions import Actions
from globals import Cameras

actions = Actions()


class Touchscreen:
    def __init__(self):
  
        captureImageButton = QPushButton('Capture Image')
        captureImageButton.clicked.connect(actions.CaptureImage)
        captureImageButton.show()

        # ------------------------------------------------------------------------------		

        captureVideoButton = QPushButton('Capture Image')
        captureVideoButton.clicked.connect(actions.CaptureVideo)
        captureVideoButton.show()

        # ------------------------------------------------------------------------------		

        shutterUpButton = QPushButton('Shutter ▲')
        shutterUpButton.clicked.connect(actions.SetShutter('up'))
        shutterUpButton.show()

        shutterDownButton = QPushButton('Shutter ▼')
        shutterDownButton.clicked.connect(actions.SetShutter('down'))
        shutterDownButton.show()

        # ------------------------------------------------------------------------------		

        isoUpButton = QPushButton('ISO ▲')
        isoUpButton.clicked.connect(actions.SetISO('up'))
        isoUpButton.show()

        isoDownButton = QPushButton('ISO ▼')
        isoDownButton.clicked.connect(actions.SetISO('down'))
        isoDownButton.show()

        # ------------------------------------------------------------------------------		

        exposureModeButton = QPushButton('Exposure Mode')
        exposureModeButton.clicked.connect(actions.SetExposureMode())
        exposureModeButton.show()

        # ------------------------------------------------------------------------------		

        meteringModeButton = QPushButton('Metering Mode')
        meteringModeButton.clicked.connect(actions.SetMeteringMode())
        meteringModeButton.show()

        # ------------------------------------------------------------------------------		

        evUpButton = QPushButton('EV ▲')
        evUpButton.clicked.connect(actions.SetExposureValue('up'))
        evUpButton.show()

        evDownButton = QPushButton('EV ▼')
        evDownButton.clicked.connect(actions.SetExposureValue('down'))
        evDownButton.show()

        # ------------------------------------------------------------------------------		

        bracketUpButton = QPushButton('Bracket ▲')
        bracketUpButton.clicked.connect(actions.SetBracket('up'))
        bracketUpButton.show()

        bracketDownButton = QPushButton('Bracket ▼')
        bracketDownButton.clicked.connect(actions.SetBracket('down'))
        bracketDownButton.show()

        # ------------------------------------------------------------------------------		

        awbModeButton = QPushButton('AWB Mode')
        awbModeButton.clicked.connect(actions.SetAWBMode())
        awbModeButton.show()

        # ------------------------------------------------------------------------------		

        timerButton = QPushButton('Timer')
        timerButton.clicked.connect(actions.SetTimer())
        timerButton.show()

        # ------------------------------------------------------------------------------		

        setStereoButton = QPushButton('Set Stereo')
        setStereoButton.clicked.connect(actions.SetStereo)
        if Cameras.count > 1:
            setStereoButton.setEnabled = False
        setStereoButton.show()

        # ------------------------------------------------------------------------------		

        toggleSettingsButton = QPushButton('Settings')
        toggleSettingsButton.clicked.connect(actions.ToggleSettings())
        toggleSettingsButton.show()