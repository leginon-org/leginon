#!/usr/bin/env python

from Tkinter import *
from ImageViewer import *

root = Tk()

iv = ImageViewer()
iv.pack()

data1 = mrc_to_numeric('test1.mrc')
data2 = mrc_to_numeric('test2.mrc')


while 1:
	iv.import_numeric(data1)
	iv.show()
	iv.update()
	root.after(500)
	iv.import_numeric(data2)
	iv.show()
	iv.update()
	root.after(500)


root.mainloop()
