#!/usr/bin/env python
# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#
# $Source: /ami/sw/cvsroot/pyleginon/calibrationclient.py,v $
# $Revision: 1.211 $
# $Name: not supported by cvs2svn $
# $Date: 2007-05-22 19:21:07 $
# $Author: pulokas $
# $State: Exp $
# $Locker:  $
"""
Interactive script to enter stage tilt speed calibration to database.
Requires knowledge of hostname and diffraction mode tem class name.
See leginon.org Issue #8621
"""
import sys
from leginon import leginondata
from leginon import calibrationclient

class Logger(object):
	def info(self,msg):
		print "INFO:", msg

	def warning(self,msg):
		print "WARNING:", msg

	def error(self,msg):
		print "ERROR:", msg

class fakeNode(object):
	def __init__(self, parent):
		self.parent = parent
		self.logger = Logger()
		self.setSessionData()

	def setSessionData(self):
		# find administrator user
		ur = leginondata.UserData(username='administrator').query()
		if ur:
			admin_user = ur[0]
		else:
			# do not process without administrator.
			print " Need administrator user to import"
			self.parent.close(True)
		q = leginondata.SessionData(user=admin_user)
		r = q.query(results=1)
		if r:
			# use any existing session.
			self.session = r[0]
		else:
			q['name']='calimport'
			q['comment'] = 'import calibrations'
			# insert as a hidden session.
			q['hidden'] = True
			q.insert()
			self.session = q

class StageTiltSpeedCalibrator(object):
	def __init__(self, params):
		try:
			self.validateInput(params)
		except ValueError, e:
			print "Error: %s" % e
			self.close(1)
		self.calclient = calibrationclient.StageSpeedClient(fakeNode(self))

	def validateInput(self, params):
		tem_hostname, tem_name = params[0], params[1]
		self.tem = self.getTemInstrumentData(tem_hostname, tem_name)

	def getTemInstrumentData(self, hostname,temname):
		if 'Diffr' not in temname:
			raise ValueError(" This calibration is for diffraction tem only")
			sys.exit()
		kwargs = {'hostname':hostname,'name':temname}
		q = leginondata.InstrumentData(hostname=hostname, name=temname)
		results = q.query(results=1)
		if not results:
			print "ERROR: incorrect hostname/scope class name...."
			r = leginondata.InstrumentData(name=temname).query(results=1)
			if r:
				raise ValueError("Try %s instead" % r[0]['hostname'])
			else:
				raise ValueError("  No %s scope found" % temname)
			sys.exit()

		sourcetem = results[0]
		return sourcetem

	def testCalibration(self, speed, target_angle):
		speed = float(speed)
		target_angle = float(target_angle)
		corrected_speed = self.calclient.getCorrectedTiltSpeed(self.tem, speed, target_angle)
		print "testing the calibration...."
		print "when moved by %.2f degrees tilt:" % target_angle
		print "  corrected speed of %.3f degrees/s is %.3f" % (speed, corrected_speed)

	def run(self):
		print self.tem.dbid
		slope = float(raw_input('Slope of time deviation at given tilt speed for the same tilt range= '))
		intercept = float(raw_input('Y-intercept of time deviation at given tilt speed for the same tilt range= '))
		self.calclient.storeSpeedCalibration(self.tem, None, 'a', slope, intercept)
		self.testCalibration(2.0,60)

	def close(self, status=0):
		if status:
			print "Exit with Error"
			sys.exit(1)

if __name__=='__main__':
	tem_host = raw_input('TEM hostname = ')
	tem_name = raw_input('TEM name = ')
	app = StageTiltSpeedCalibrator((tem_host, tem_name))
	app.run()
	app.close()
	 
