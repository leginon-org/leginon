#!/usr/bin/env python
import manager
import nodegui
import sys
import Tkinter
import time
import os
import socket

if __name__ == '__main__':

	m = manager.Manager(('manager',))

	# quite hackish for now
	try:
		appfile = sys.argv[1]
		m.app.load(appfile)
		print m.app.getLaunchers()
		for l in m.app.getLaunchers():
	#		if l[0] == 'manager':
	#			# if its in the manager's process, it must be started
	#			m.newLauncher(l)
	#			while l not in m.clients:
	#				time.sleep(0.1)
	#		else:
				# if not, try to add it at a standard port
			try:
				m.addNode(l[-1], 55555)
				while l not in m.clients:
					time.sleep(0.1)
			except:
				# if its was on this machine, exec it
				if socket.gethostname() == l[-1]:
					print "Attempting to create local launcher process..."
					if sys.platform == 'win32':
						os.spawnve(os.P_NOWAIT, 'c:\\Python22\\python.exe',
							#['launcher.py', 'c:\\dev\\pyleginon\\launcher.py', '55555'],
							['launcher.py', '\\\\colossus\\amishare\\suloway\\pyleginon\\launcher.py', '55555'],
							os.environ)
					else:
						os.spawnv(os.P_NOWAIT, 'launcher.py', ['launcher.py', '55555'])
					while l not in m.clients:
						try:
							m.addNode(l[-1], 55555)
						except:
							time.sleep(0.25)
				else:
					print 'Unable to activate launcher %s' % l
		m.app.launch()
	except IndexError:
		print "Attempting to create local launcher process..."
		if sys.platform == 'win32':
			os.spawnve(os.P_NOWAIT, 'c:\\Python22\\python.exe',
#				['launcher.py', 'c:\\dev\\pyleginon\\launcher.py', '55555'], os.environ)
				['launcher.py', '\\\\colossus\\amishare\\suloway\\pyleginon\\launcher.py', '55555'], os.environ)
		else:
			os.spawnv(os.P_NOWAIT, 'launcher.py', ['launcher.py', '55555'])
		l = (socket.gethostname(),)
		while l not in m.clients:
			try:
				m.addNode(l[-1], 55555)
			except:
				time.sleep(0.25)

	#m.start()

	root = Tkinter.Tk()
	root.wm_title('Node GUI Launcher')

	loc = m.location()
	# jorg
	time.sleep(1.0)
	gui = nodegui.NodeUILauncher(root, loc['hostname'], loc['UI port'])
	gui.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)
	root.mainloop()
	m.exit() 

