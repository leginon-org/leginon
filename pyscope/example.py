#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import client
import Tkinter
import array
import base64

# EDIT the hostnames and ports to match where the server is running
scopeclient = client.client('http://amilab2:8000')
cameraclient = client.client('http://amilab2:8001')

# set the image dimesions
cameraclient['x dimension'] = 256
cameraclient['y dimension'] = 256

# set exposure time to greater than 1000ms otherwise DM simulation
# will yield a dark image
cameraclient['exposure time'] = 1000

# get the current image dimensions
xdim = cameraclient['x dimension']
ydim = cameraclient['y dimension']
# get the image data, a base64 encoded ushort array
# base64 encoding is not the most efficient way, but to make XML-RPC
# happy this is the way it is for now
print "Acquiring and decoding image...",
image = array.array('H', base64.decodestring(cameraclient['image data']))
print "Done."

# start the Tk, app
root = Tkinter.Tk()
root.title("Example pyScope Client")
canvas = Tkinter.Canvas(root, width=xdim, height=ydim)
canvas.pack()

# display the image on the canvas by drawing point by point
# this is quite ineffiecient, which is why it is only an example
print "Displaying image...",
for y in range(ydim):
  for x in range(xdim):
    color = image[x + y*xdim]
    canvas.create_line(x,y,x+1,y+1,fill="#%x%x%x" % (color, color, color))
print "Done."

# add some text with current microscope values, and some image info
canvas.create_text(16, 16,
                   text='Magnification = %.1fX\nHigh Tension = %dkV\nX = %d, Y = %d\nWidth = %d, Height = %d'
                        % (scopeclient['magnification'],
                           scopeclient['high tension']/1000,
			   cameraclient['x offset'],
			   cameraclient['y offset'],
			   cameraclient['x dimension'],
                           cameraclient['y dimension']),
                   fill='red', anchor='nw')

# loop for events
root.mainloop()

