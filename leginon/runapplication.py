#!/usr/bin/env python
import manager
import nodegui
import sys
import Tkinter
import time
import os
import socket

def addNode(id, hostname, port):
	while id not in m.clients:
		try:
			m.addNode(hostname, port)
		except:
			time.sleep(0.1)

def createlauncher(id, hostname, port):
	if socket.gethostname() != hostname:
		return False
	#launcherpath = 'c:\\dev\\pyleginon\\launcher.py'
	launcherpath = '\\\\colossus\\amishare\\suloway\\pyleginon\\launcher.py'

	print 'Attempting to spawn launcher process'
	if sys.platform == 'win32':
		os.spawnve(os.P_NOWAIT, 'c:\\Python22\\python.exe',
				['launcher.py', launcherpath, str(port)], os.environ)
	else:
		os.spawnv(os.P_NOWAIT, 'launcher.py', ['launcher.py', str(port)])
	addNode(id, hostname, port)
	print 'Launcher process spawned'
	return True

if __name__ == '__main__':

	print 'Creating manager'
	m = manager.Manager(('manager',))
	print 'Manager creation successful'

	# quite hackish for now
	try:
		appfile = sys.argv[1]
		print 'Attempting to load application: %s' % appfile
		m.app.load(appfile)
		print 'Load successful'
		print m.app.getLaunchers()
		for l in m.app.getLaunchers():
			# try to add launcher at a standard port
			hostname = l[-1]
			port = 55555
			try:
				print 'Trying to contact launcher %s at %s:%s' % (l, hostname, port)
				addNode(l, hostname, port)
			except:
				print 'Contact launcher %s at %s:%s failed' % (l, hostname, port)
				if not createlauncher(l, hostname, port):
					print 'Error: launcher %s is not available' % l
		m.app.launch()
	except IndexError:
		hostname = socket.gethostname()
		port = 55555
		createlauncher((hostname,), hostname, port)

	#m.start()

	root = Tkinter.Tk()
	root.wm_title('Node GUI Launcher')

	loc = m.location()
	# jorg
	#time.sleep(1.0)
	gui = nodegui.NodeUILauncher(root, loc['hostname'], loc['UI port'])
	gui.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
	root.mainloop()
	m.exit() 

