#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
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

		container = uidata.LargeContainer('Intensity Calibrator')
		#container.addObjects((cameraconfig, calimage))
		self.uiserver.addObject(container)
