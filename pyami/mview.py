#!/usr/bin/env python

from Tkinter import *
from ImageViewer import *
import MySQLdb

root = Tk()

iv = ImageViewer(root)
iv.pack()

#data1 = mrc_to_numeric('test1.mrc')
#data2 = mrc_to_numeric('test2.mrc')

def import_mrc(viewer, filename):
	data = mrc_to_numeric(filename)
	viewer.import_numeric(data)
	viewer.show()
	viewer.update()

while 1:
	import_mrc(iv,'test1.mrc')
	root.after(500)
	import_mrc(iv,'test2.mrc')
	root.after(500)

root.mainloop()
