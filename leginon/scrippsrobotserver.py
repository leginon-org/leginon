#!/usr/bin/env python
import robotserver
try:
	import pythoncom
	import win32com.client
except:
	print 'no pythoncom or win32com.  robot will be simulated'
	pythoncom = None

robotattrs = ['Signal' + str(i) for i in range(0,13)]
robotattrs.append('gridNumber')

class FakeCommunication(object):
	pass
for attr in robotattrs:
	setattr(FakeCommunication, attr, 0)

class ScrippsRobotServer(robotserver.RobotServer):
	def __init__(self):
		robotserver.RobotServer.__init__(self)
		if pythoncom is None:
			self.communication = FakeCommunication()
		else:
			pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
			self.communication = win32com.client.Dispatch('RobotCommunications.Signal')
		initialstatus = [(attr,None) for attr in robotattrs]
		self.status = dict(initialstatus)

	def getStatus(self):
		status = [(attr,getattr(self.communication, attr)) for attr in robotattrs]
		return dict(status)

	def checkRobot(self):
		changed = []
		newstatus = self.getStatus()
		for attr,newvalue in newstatus.items():
			if newvalue != self.status[attr]:
				print '%s changed:  %s  ->  %s' % (attr, self.status[attr], newvalue)
				changed.append((attr,newvalue))
		self.status = newstatus
		return changed

for attr in robotattrs:
	# localattr allows a value of attr now to be used in the function
	# not the value of attr later
	# maybe try using new.instancemethod here
	def newmethod(self, value, localattr=attr):
		print 'handling %s set to %s' % (localattr, value)
		setattr(self.communication, localattr, value)
	methodname = 'handle_' + attr
	setattr(ScrippsRobotServer, methodname, newmethod)

if __name__ == '__main__':
	s = ScrippsRobotServer()
	print 'entering main loop'
	s.mainloop()
