import calibrator
import calibrationclient

class IntensityCalibrator(calibrator.Calibrator):
	def __init__(self, id, session, nodelocations, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, nodelocations, **kwargs)


		self.calclient = calibrationclient.IntensityCalibrationClient(self)


		self.defineUserInterface()
		self.start()


	def defineUserInterface(self):
		calibrator.Calibrator.defineUserInterface(self)

		container = uidata.UIMediumContainer('Intensity Calibrator')
		#container.addUIObjects((cameraconfig, calimage))
		self.uiserver.addUIObject(container)
