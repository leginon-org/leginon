#!/usr/bin/env python

import sys
if len(sys.argv) != 3:
	print 'usage:  %s host port' % sys.argv[0]
	sys.exit(1)

from Tkinter import *
from xmlrpcnode import *


host = sys.argv[1]
port = int(sys.argv[2])

top = Tk()
gui = xmlrpcgui(top, host, port)
gui.pack()

top.mainloop()
