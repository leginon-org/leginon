#!/usr/bin/env python

import numpy
import scipy.linalg

## calibrate center of rotation

class BetaRotation(object):
	def __init__(self):
		self.filename = 'betacenter.txt'
		self.center = None   # not calibrated
		print ''
		try:
			self.load_center()
			print 'Beta center loaded from file:', self.center
		except:
			print 'No beta center loaded...  you must calibrate.'

	def main_loop(self):
		while True:
			print '''
			Enter 1 to calibrate center of rotation.
			Enter 2 to calculate rotated position.
			'''
			choice = raw_input('choice: ')
			if choice == '1':
				self.calibrate()
			elif choice == '2':
				self.calculate()
			else:
				print ''
				continue

	def load_center(self):
		f = open(self.filename)
		line = f.read()
		line = line.strip()
		splitline = line.split()
		self.center = map(float, splitline)

	def save_center(self):
		if self.center is None:
			print 'No center calibrated.  Cannot save'
			return
		f = open(self.filename, 'w')
		line = '%f %f' % self.center
		f.write(line)
		f.close()

	def calculate(self):
		if self.center is None:
			print 'Need to calibrate first.'
			return

		print 'Enter position at original position.'
		print ''
		beta0 = raw_input('Object B position (degrees): ')
		xpos0 = raw_input('Object X position (micron): ')
		ypos0 = raw_input('Object Y position (micron): ')
		beta0 = float(beta0)
		xpos0 = float(xpos0)
		ypos0 = float(ypos0)
		print ''
		beta1 = raw_input('Enter new beta rotation angle: ')
		print ''
		beta1 = float(beta1)

		beta = beta1 - beta0
		beta = beta * numpy.pi / 180.0
		vectx0 = xpos0 - self.center[0]
		vecty0 = ypos0 - self.center[1]
		vectx1 = vectx0 * numpy.cos(beta) - vecty0 * numpy.sin(beta)
		vecty1 = vectx0 * numpy.sin(beta) + vecty0 * numpy.cos(beta)
		x1 = vectx1 + self.center[0]
		y1 = vecty1 + self.center[1]
		print ''
		print 'Rotated position: ', x1, y1
		return x1,y1

	def calibrate(self):
		print ''
		print 'Calibrating Center of Beta Rotation'
		# center object
		print ''
		print 'Center object, then enter stage position Beta, X, Y.'
		print ''
		beta0 = raw_input('Object B position (degrees): ')
		xpos0 = raw_input('Object X position (micron): ')
		ypos0 = raw_input('Object Y position (micron): ')
		print ''
		beta0 = float(beta0)
		xpos0 = float(xpos0)
		ypos0 = float(ypos0)

		# rotate and center again
		print 'Rotate beta by at least 90 degrees and recenter object.'
		print 'Enter stage position Beta, X, Y.'
		print ''
		beta1 = raw_input('Object B position (degrees): ')
		xpos1 = raw_input('Object X position (micron): ')
		ypos1 = raw_input('Object Y position (micron): ')
		print ''
		beta1 = float(beta1)
		xpos1 = float(xpos1)
		ypos1 = float(ypos1)

		# rotation in radian
		beta = beta1 - beta0
		beta = beta * numpy.pi / 180.0

		# calculate rotation center
		m11 = 1 - numpy.cos(beta)
		m12 = numpy.sin(beta)
		m21 = -numpy.sin(beta)
		m22 = 1 - numpy.cos(beta)
		m = numpy.array(((m11,m12),(m21,m22)))
		minv = scipy.linalg.inv(m)

		c1 = ypos0 * numpy.sin(beta) - xpos0 * numpy.cos(beta) + xpos1
		c2 = -ypos0 * numpy.cos(beta) - xpos0 * numpy.sin(beta) + ypos1

		center = numpy.dot(minv, (c1,c2))
		self.center = center[0], center[1]
		print 'Calibrated center: ', self.center
		self.save_center()


if __name__ == '__main__':
	b = BetaRotation()
	b.main_loop()
