#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
'''
'''

import calibrator
import Numeric
import LinearAlgebra
import data
import calibrationclient
import uidata

class BeamTiltCalibrator(calibrator.Calibrator):
	'''
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		calibrator.Calibrator.__init__(self, id, session, nodelocations, **kwargs)


		self.calclient = calibrationclient.BeamTiltCalibrationClient(self)
		self.euclient = calibrationclient.EucentricFocusClient(self)


		self.defineUserInterface()
		self.start()

	def calibrateAlignment(self, tilt_value):
		self.cam.uiApplyAsNeeded()

		state1 = {'beam tilt': tilt_value}
		state2 = {'beam tilt': -tilt_value}

		matdict = {}

		for axis in ('x','y'):
			print 'measuring %s tilt' % (axis,)

			diff1 = self.calclient.measureDispDiff(axis, tilt_value, tilt_value)
			diff2 = self.calclient.measureDispDiff(axis, -tilt_value, tilt_value)

			matcol = self.calclient.eq11(diff1, diff2, 0, 0, tilt_value)
			matdict[axis] = matcol

		print 'making matrix'
		matrix = Numeric.zeros((2,2), Numeric.Float32)
		print 'matrix type', matrix.typecode()
		print 'matdict type', matdict['x'].typecode()
		matrix[:,0] = matdict['x']
		matrix[:,1] = matdict['y']

		## store calibration
		print 'storing calibration'
		mag = self.getMagnification()
		ht = self.getHighTension()
		self.calclient.storeMatrix(ht, mag, 'coma-free', matrix)
		return ''

	def calibrateDefocus(self, tilt_value, defocus1, defocus2):
		self.cam.uiApplyAsNeeded()
		state1 = {'defocus': defocus1}
		state2 = {'defocus': defocus2}
		matdict = {}
		for axis in ('x','y'):
			print 'measuring %s tilt' % (axis,)
			shift1, shift2 = self.calclient.measureDisplacements(axis, tilt_value, state1, state2)
			matcol = self.calclient.eq11(shift1, shift2, defocus1, defocus2, tilt_value)
			matdict[axis] = matcol
		print 'making matrix'
		matrix = Numeric.zeros((2,2), Numeric.Float32)
		print 'matdict type', matdict['x'].typecode()

		m00 = float(matdict['x'][0])
		m10 = float(matdict['x'][1])
		m01 = float(matdict['y'][0])
		m11 = float(matdict['y'][1])
		matrix = Numeric.array([[m00,m01],[m10,m11]],Numeric.Float32)

		## store calibration
		print 'storing calibration'
		ht = self.getHighTension()
		mag = self.getMagnification()
		print 'MATRIX', matrix
		print 'MATRIX shape', matrix.shape
		print 'MATRIX type', matrix.typecode()
		print 'MATRIX flat', Numeric.ravel(matrix)
		self.calclient.storeMatrix(ht, mag, 'defocus', matrix)
		return ''

	def calibrateStigmators(self, tilt_value, delta):
		self.cam.uiApplyAsNeeded()

		currentstig = self.getObjectiveStigmator()
		## set up the stig states
		stig = {'x':{}, 'y':{}}
		for axis in ('x','y'):
			for sign in ('+','-'):
				stig[axis][sign] = dict(currentstig)
				if sign == '+':
					stig[axis][sign][axis] += delta/2.0
				elif sign == '-':
					stig[axis][sign][axis] -= delta/2.0

		for stigaxis in ('x','y'):
			print 'calculating matrix for stig %s' % (stigaxis,)
			matdict = {}
			for tiltaxis in ('x','y'):
				print 'measuring %s tilt' % (tiltaxis,)
				stig1 = stig[stigaxis]['+']
				stig2 = stig[stigaxis]['-']
				state1 = data.ScopeEMData(id=('scope',),stigmator={'objective':stig1})
				state2 = data.ScopeEMData(id=('scope',),stigmator={'objective':stig2})
				shift1, shift2 = self.calclient.measureDisplacements(tiltaxis, tilt_value, state1, state2)
				print 'shift1', shift1
				print 'shift2', shift2
				stigval1 = stig1[stigaxis]
				stigval2 = stig2[stigaxis]
				matcol = self.calclient.eq11(shift1, shift2, stigval1, stigval2, tilt_value)
				matdict[tiltaxis] = matcol
			matrix = Numeric.zeros((2,2), Numeric.Float32)
			matrix[:,0] = matdict['x']
			matrix[:,1] = matdict['y']

			## store calibration
			mag = self.getMagnification()
			ht = self.getHighTension()
			type = 'stig' + stigaxis
			self.calclient.storeMatrix(ht, mag, type, matrix)

		## return to original stig
		stigdict = {'stigmator':{'objective':currentstig}}
		stigdata = data.ScopeEMData(id=('scope',), initializer=stigdict)
		self.publishRemote(stigdata)
		return ''

	def measureDefocusStig(self, btilt):
		self.cam.uiApplyAsNeeded()
		try:
			ret = self.calclient.measureDefocusStig(btilt)
		except:
			self.printException()
			ret = {}
		print 'RET', ret
		return ret

	def getDefocus(self):
		emdata = self.researchByDataID(('defocus',))
		return emdata

	def getObjectiveStigmator(self):
		emdata = self.researchByDataID(('stigmator',))
		obj = dict(emdata['stigmator']['objective'])
		return obj

	def defineUserInterface(self):
		calibrator.Calibrator.defineUserInterface(self)
		self.defocustiltvalue = uidata.Float('Tilt', 0.01, 'rw', persist=True)
		self.defocus1 = uidata.Float('Defocus 1', -1e-6, 'rw', persist=True)
		self.defocus2 = uidata.Float('Defocus 2', -2e-6, 'rw', persist=True)
		caldefocusmethod = uidata.Method('Calibrate',
																				self.uiCalibrateDefocus)
		defocuscontainer = uidata.Container('Defocus')
		defocuscontainer.addObjects((self.defocustiltvalue,
																		self.defocus1, self.defocus2,
																		caldefocusmethod))

		self.stigtiltvalue = uidata.Float('Stigmator Tilt', 0.01, 'rw', persist=True)
		self.stigdelta = uidata.Float('Stigmator Delta', 0.2, 'rw', persist=True)
		calstigmethod = uidata.Method('Calibrate Stigmators',
																		self.uiCalibrateStigmators)
		stigcontainer = uidata.Container('Stigmator')
		stigcontainer.addObjects((self.stigtiltvalue, self.stigdelta,
																calstigmethod))

		self.measuretiltvalue = uidata.Float('Measure Tilt', 0.01, 'rw')
		self.resultvalue = uidata.Struct('Necessary Correction', {}, 'r')
		measuremethod = uidata.Method('Measure', self.uiMeasureDefocusStig)
		correctdefocusmethod = uidata.Method('Correct Defocus', self.uiCorrectDefocus)
		correctstigmethod = uidata.Method('Correct Stigmator', self.uiCorrectStigmator)
		resetdefocusmethod = uidata.Method('Reset Defocus', self.uiResetDefocus)
		measurecontainer = uidata.Container('Measure')
		measurecontainer.addObjects((self.measuretiltvalue, self.resultvalue, measuremethod, correctdefocusmethod, correctstigmethod, resetdefocusmethod))

		## eucentric focus stuff
		euc = uidata.Container('Eucentric Focus')
		eufromscope = uidata.Method('Record Current Focus as Eucentric Focus', self.uiEucFromScope)
		eutoscope = uidata.Method('Send Recorded Eucentric Focus to Scope', self.uiEucToScope)
		self.eucstatus = uidata.MessageLog('Status')

		euc.addObjects((eufromscope,eutoscope, self.eucstatus))

		container = uidata.LargeContainer('Beam Tilt Calibrator')
		container.addObjects((defocuscontainer, stigcontainer, measurecontainer, euc))
		self.uiserver.addObject(container)

	def uiCalibrateDefocus(self):
		self.calibrateDefocus(self.defocustiltvalue.get(),
													self.defocus1.get(),
													self.defocus2.get())

	def uiCalibrateStigmators(self):
		self.calibrateStigmators(self.stigtiltvalue.get(),
													self.stigdelta.get())

	def uiMeasureDefocusStig(self):
		result = self.measureDefocusStig(self.measuretiltvalue.get())
		self.resultvalue.set(result)

	def uiCorrectDefocus(self):
		delta = self.resultvalue.get()
		if not delta:
			print 'no result, you must measure first'
			return
		current = self.getCurrentValues()	

		newdefocus = current['defocus'] + delta['defocus']
		newdata = data.ScopeEMData(id=('scope',), defocus=newdefocus)
		self.publishRemote(newdata)

	def uiCorrectStigmator(self):
		delta = self.resultvalue.get()
		if not delta:
			print 'no result, you must measure first'
			return
		current = self.getCurrentValues()	

		newstigx = current['stigx'] + delta['stigx']
		newstigy = current['stigy'] + delta['stigy']
		stigdict = {'stigmator': {'objective': {'x':newstigx,'y':newstigy}}}
		newdata = data.ScopeEMData(id=('scope',), initializer=stigdict)
		self.publishRemote(newdata)

	def uiResetDefocus(self):
		newemdata = data.ScopeEMData(id=('scope',))
		newemdata['reset defocus'] = True
		self.publishRemote(newemdata)

	def getCurrentValues(self):
		defocusdata = self.researchByDataID(('defocus',))
		defocus = defocusdata['defocus']
		stigdata = self.researchByDataID(('stigmator',))
		stig = stigdata['stigmator']['objective']
		stigx = stig['x']
		stigy = stig['y']
		return {'defocus':defocus, 'stigx':stigx, 'stigy':stigy}

	def uiEucToScope(self):
		self.eucToScope()

	def uiEucFromScope(self):
		self.eucFromScope()

	def eucToScope(self):
		scope = self.researchByDataID(('scope',))
		ht = scope['high tension']
		mag = scope['magnification']
		eudata = self.euclient.researchEucentricFocus(ht,mag)
		focus = eudata['focus']

		scopedata = data.ScopeEMData()
		scopedata['id'] = ('scope',)
		scopedata['focus'] = focus
		try:
			self.publishRemote(scopedata)
		except node.PublishError:
			self.printException()
			self.messagelog.error('Cannot set instrument parameters')

	def eucFromScope(self):
		## get current value of focus
		scope = self.researchByDataID(('scope',))
		ht = scope['high tension']
		mag = scope['magnification']
		focus = scope['focus']
		self.euclient.publishEucentricFocus(ht, mag, focus)
		self.eucstatus.information('published:  HT: %s, Mag: %s, Euc. Focus: %s' % (ht, mag, focus))


