#!/usr/bin/python
import math
import numpy

class BeamTiltCtfData(object):
	def __init__(self, btxy_radians, defocus1_m, defocus2_m, astig_angle_degrees):
		self.bt = btxy_radians # xy dict
		self.defocus = (defocus1_m+defocus2_m)/2 # meters
		self.astig_angle = math.radians(astig_angle_degrees)
		self.astig_magnitude = (defocus1_m-defocus2_m)/2
		self.astig = {'x': self.astig_magnitude*math.cos(2*self.astig_angle),
									'y': self.astig_magnitude*math.sin(2*self.astig_angle),
								}

class AberrationEstimator(object):
	def __init__(self, cs=2.7e-3, ht=300000):
		self.cs = cs
		self.data = []

	def resetData(self):
		self.data = []

	def addData(self,bt_xy, ctfresult):
		r= ctfresult
		bdata = BeamTiltCtfData(bt_xy, r['defocus1'],r['defocus2'],r['angle_astigmatism'])
		self.data.append(bdata)

	def getFullTiltListFromData(self, bdata):
		'''
		return list of list of the coefficients based on Juri Barthel thesis
		tilted_aberration = tilt_coefficients * 0tilt_aberration
		'''
		tx=bdata.bt['x']
		ty=bdata.bt['y']
		tx2=tx*tx
		ty2=ty*ty
		tx3=tx2*tx
		ty3=ty2*ty
		txy=tx*ty
		# aberration map in the row.
		self.Amap = {'defocus':0,
								'astig x':1,'astig y':2,
								'coma x':3,'coma y':4,
								'3fold x':5,'3fold y':6,
								'cs':7,
								'star x':8,'star y':9,
								'4fold':10,'4fold y':11,
							}
		# shift x
		a0 = [tx,tx,ty,tx2+ty2/3,2*txy/3,tx2-ty2,2*txy,tx*(tx2+ty2),tx3,0.5*(3*tx2*ty+ty3),tx3-3*tx*ty2,3*tx2*ty-ty3]
		# shift y
		a1 = [ty,-ty,tx,2*txy/3,tx2/3+ty2,-2*txy,tx2-ty2,ty*(tx2+ty2),-ty3,0.5*(tx3+3*tx*ty2),-3*tx2*ty+ty3,tx3-3*tx*ty2]
		# defocus
		a2 = [1,0,0,4*tx/3,4*ty/3,0,0,2*(tx2+ty2),1.5*(tx2-ty2),3*txy,0,0]
		# 2fold astig x
		a3 = [0,1,0,2*tx/3,-2*ty/3,2*tx,2*ty,tx2-ty2,1.5*(tx2+ty2),0,3*(tx2-ty2),6*txy]
		# 2fold astig y
		a4 = [0,0,1,2*ty/3,-2*tx/3,-2*ty,2*tx,2*txy,0,3*(tx2+ty2)/2,-6*txy,3*(tx2-ty2)]
		# coma x
		a5 = [0,0,0,1,0,0,0,3*tx,9*tx/4,9*ty/4,0,0]
		# coma y
		a6 = [0,0,0,0,1,0,0,3*ty,-9*ty/4,9*tx/4,0,0]
		alist = [a0,a1,a2,a3,a4,a5,a6]
		return alist

	def popAmap(self):
		'''
		Pop the key,value pair where value is 0.
		'''
		newmap = dict(self.Amap)
		for k in self.Amap:
			if self.Amap[k] == 0:
				del newmap[k]
		for k in newmap.keys():
			newmap[k] -= 1
		self.Amap = dict(newmap)

	def makeTiltCoefficientMatrix(self):
		'''
		create M,5 coefficient matrix based on the beam tilt
		'''
		fulllist = []
		for bdata in self.data:
			alist = self.getFullTiltListFromData(bdata)
			# use only defocus, astig x and astig y results for fitting.
			sublist = map((lambda x: x[:8]),alist[2:5])
			fulllist.extend(sublist)
		m = numpy.matrix(fulllist)
		return m

	def makeTiltCtfMatrix(self):
		'''
		create M,1 matrix of M ctf measurement from the beam tilt.
		'''
		alist = []
		for bdata in self.data:
			alist.extend([bdata.defocus,bdata.astig['x'], bdata.astig['y']])
			m = numpy.matrix(alist)
		return m.T

	def removeKnownTerm(self,tiltmatrix, ctfmatrix, last=True, value=0):
		'''take off first or last term with known value'''
		length = tiltmatrix.shape[1]
		if last:
			index = length-1
			start = 0
			end = index
		else:
			start = 1
			end = length
			index = 0
			self.popAmap()
		for i in range(ctfmatrix.shape[0]):
			ctfmatrix[i] -= tiltmatrix[i,index]*value
		return tiltmatrix[:,start:end], ctfmatrix
	
	def solveAberration(self,tiltmatrix,ctfmatrix):
		'''
		Solve aberration with least square fit.
		'''
		# plug-in cs value to increase data/parameter ratio
		a, b = self.removeKnownTerm(tiltmatrix, ctfmatrix,True, self.cs)
		A, residual, rank, s = numpy.linalg.lstsq(a,b, rcond=-1)
		return A, residual

	def mapAberration(self,A):
		'''
		return dictionary of the aberration.
		'''
		m = self.Amap
		r = {}
		r['defocus'] = A[m['defocus'],0]
		r['astig'] = {'x':A[m['astig x'],0],'y':A[m['astig y'],0]}
		r['coma'] = {'x':A[m['coma x'],0],'y':A[m['coma y'],0]}
		r['3fold astig'] = {'x':A[m['3fold x'],0],'y':A[m['3fold y'],0]}
		return r

	def calculateBeamTiltCorrection(self,A):
		'''
		beam tilt that will make the tilted coma to become zero.
		It ignores higher order terms.
		'''
		tx = -A[self.Amap['coma x'],0]/(3*self.cs)
		ty = -A[self.Amap['coma y'],0]/(3*self.cs)
		return {'x':tx, 'y':ty}

	def run(self):
		if len(self.data) < 5:
			raise ValueError('Not enough good fit to estimate aberration required')
		tiltmatrix = self.makeTiltCoefficientMatrix()
		ctfmatrix = self.makeTiltCtfMatrix()
		A, residual = self.solveAberration(tiltmatrix,ctfmatrix)
		return A

if __name__ == '__main__':
	app = AberrationEstimator()
	# fake data test
	from pyami import ctfestimator
	app1 = ctfestimator.GctfEstimator()
	from leginon import leginondata
	imagedata = leginondata.AcquisitionImageData().query(results=1)[0]
	t = 0.005
	btilts = [(0.0,0.0),(t,0),(0,t),(-t,0),(0,-t)]
	for v in btilts:
		btxy = {'x':float(v[0]),'y':float(v[1])}
		ctfresult = app1.fakeRunOneImageData(imagedata)
		app.addData(btxy,ctfresult)
	print app.run()
