#!/usr/bin/env python

from Mrc import *
from Numeric import *
from Tkinter import *
from ImageViewer import ImageCanvas

root = Tk()

can = ImageCanvas(root, bg='blue')
can.pack()

im1 = can.create_image_item(0, 0)
im2 = can.create_image_item(256, 256)

data1 = mrc_to_numeric('test1.mrc')
data1 = data1[:256]
data2 = mrc_to_numeric('test2.mrc')
data2 = data1[:256]

im1.import_numeric(data1)
im2.import_numeric(data2)

root.mainloop()
