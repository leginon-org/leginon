from wxPython.wx import *
import wxImageViewer
import Numeric, umath
import Mrc
import holefinderback

def circlePoints(numericimage, cx, cy, x, y):
	if x == 0:
		numericimage[cy + y, cx] = 256
		numericimage[cy + y, cx] = 256
		numericimage[cy, cx + y] = 256
		numericimage[cy, cx - y] = 256
	elif x == y:
		numericimage[cy + y, cx + x] = 256
		numericimage[cy + y, cx - x] = 256
		numericimage[cy - y, cx + x] = 256
		numericimage[cy - y, cx - x] = 256
	elif x < y:
		numericimage[cy + y, cx + x] = 256
		numericimage[cy + y, cx - x] = 256
		numericimage[cy - y, cx + x] = 256
		numericimage[cy - y, cx - x] = 256
		numericimage[cy + x, cx + y] = 256
		numericimage[cy + x, cx - y] = 256
		numericimage[cy - x, cx + y] = 256
		numericimage[cy - x, cx - y] = 256

def circle(numericimage, radius, xcenter, ycenter):
	x = 0
	y = radius
	#ycenter = numericimage.shape[0]/2
	#xcenter = numericimage.shape[1]/2
	p = (5 - radius*4)/4
	circlePoints(numericimage, xcenter, ycenter, x, y)
	while x < y:
		x += 1
		if p < 0:
			p += 2*x + 1
		else:
			y -= 1
			p += 2*(x - y) + 1
		circlePoints(numericimage, xcenter, ycenter, x, y)

def gradient(image):
	m, n = image.shape

	J = Numeric.zeros((m+2, n+2), 'd')
	J[0, 0] = image[0, 0]
	J[0, 1:n + 1] = image[0]
	J[0, n + 1] = image[0, n - 1]
	J[1:m + 1, 0] = image[0:n,0]
	J[1:m + 1, 1:n + 1] = image
	J[1:m + 1, n + 1] = image[0:n, n - 1]
	J[m + 1, 0] = image[m - 1, 0]
	J[m + 1, 1:n + 1] = image[m - 1]
	J[m + 1, n + 1] = image[m - 1, n - 1]

	Ix = Numeric.zeros(J.shape, 'd')
	Ix[0:m+2,1:n+1] = (J[0:m+2,2:n+2] - J[0:m+2,0:n]) * 0.5
	Ix[0:m+2, 0] = Ix[0:m+2, 1]
	Ix[0:m+2, n+1] = Ix[0:m+2, n]

	Iy = Numeric.zeros(J.shape, 'd')
	Iy[1:m+1,0:n+2] = (J[2:m+2,0:n+2] - J[0:m,0:n+2]) * 0.5
	Iy[0, 0:n+2] = Iy[1, 0:n+2]
	Iy[m+1, 0:n+2] = Iy[m, 0:n+2]

	I_grad = Numeric.sqrt(Ix*Ix + Iy*Iy)

	return I_grad

def edges(image):
	hf = holefinderback.HoleFinder()
	hf['original'] = image
	hf.configure_edges(filter='sobel',
											size=9,
											sigma=1.4,
											absvalue=False,
											lp=True,
											lpn=5,
											lpsig=1.0)
	hf.find_edges()
	return hf['edges']


def hough(image, threshold, radius=None, radiusrange=None):

	m, n = image.shape

	if radius is None:
		if radiusrange is None:
			R = (0, min(m, n)/2)
		else:
			R = radiusrange
		M = Numeric.zeros((m, n, R[1] - R[0] + 1))
	else:
		M = Numeric.zeros(image.shape)

#	e = edges(image)
#	I_grad = gradient(e)
#	return e, I_grad

	I_grad = gradient(image)

	for i in range(0, m):
		print i
		for j in range(0, n):
			if I_grad[i, j] > threshold:
				if radius is None:
					for radius in range(R[0], R[1]):
						for x in range(i-radius, i+radius):
							vote(M, m, n, i, j, x, radius, 0) #radius-R[0])
				else:
					for x in range(i-radius, i+radius):
						vote(M, m, n, i, j, x, radius)

	if len(M.shape) == 3:
		return I_grad, M[:,:,0]
	return I_grad, M

def vote(M, m, n, i, j, x, radius, layer=None):
	y = radius**2 - (x - i)**2

#	y = Numeric.absolute(y)
	if y < 0:
		return

	y = int(Numeric.floor(Numeric.sqrt(y) + 0.5)) + j

	#y = int(Numeric.floor(Numeric.sqrt(radius**2-(x-i)**2)+0.5)+j)

	if x >= 0 and x < m and y >= 0 and y < n:
		if layer is not None:
			M[x, y, layer] = M[x, y, layer] + 1
		else:
			M[x, y] = M[x, y] + 1

if __name__=='__main__':
	m = Mrc.mrc_to_numeric('hftest.mrc')[256:768,256:768]
	m, m2 = hough(m, 100, None, [24,29])
	m2 = Numeric.clip(m2, 40, 1000)

	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Image Viewer')
			self.SetTopWindow(frame)
			self.panel = wxScrolledWindow(frame, -1)
			self.panel.SetScrollRate(5, 5)
			self.sizer = wxBoxSizer(wxHORIZONTAL)
			self.iv1 = wxImageViewer.ImagePanel(frame, -1)
			self.sizer.Add(self.iv1)
			self.iv2 = wxImageViewer.ImagePanel(frame, -1)
			self.sizer.Add(self.iv2)
			self.sizer.Layout()
			self.panel.SetSizer(self.sizer)
			self.panel.Show(true)
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)
	app.iv1.setNumericImage(m)
	app.iv2.setNumericImage(m2)
	app.MainLoop()

