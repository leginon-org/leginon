#!/usr/bin/env python
import robotserver
try:
	import pythoncom
except:
	print 'no pythoncom.  robot will be simulated'
	pythoncom = None

robotattrs = ['Signal' + str(i) for i in range(0,13)]

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
		initialstatus = self.getStatus()
		self.status = initialstatus

	def getStatus(self):
		status = [(attr,getattr(self.communication, attr)) for attr in robotattrs]
		return dict(status)

	def checkRobot(self):
		changed = []
		newstatus = self.getStatus()
		for attr,newvalue in newstatus.items():
			if newvalue != self.status[attr]:
				changed.append((attr,newvalue))
		return changed

for attr in robotattrs:
	# localattr allows a value of attr now to be used in the function
	# not the value of attr later
	def newmethod(self, value, localattr=attr):
		setattr(self.communication, localattr, value)
	methodname = 'handle_' + attr
	setattr(ScrippsRobotServer, methodname, newmethod)

if __name__ == '__main__':
	s = ScrippsRobotServer()
	s.mainloop()
