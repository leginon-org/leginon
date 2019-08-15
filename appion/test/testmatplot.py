#!/usr/bin/env python
import numpy as np
import os
#to generate 2D map from local refine
from matplotlib import use
use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
print('numpy version is %s' % np.__version__)
import matplotlib
print('matplotlib version is %s' % matplotlib.__version__)

class TestMatPlotLib(object):
	def run(self):
		size = 512
		fbase = 'matplottest'
		map_array = np.ones((size,size))
		map_array[size/4:size*3/4,size/4:size*3/4]=2
		map_array[size*3/8:size*5/8,size*3/8:size*5/8]=3
		self.plotGridContour(map_array,fbase)

	def plotGridContour(self,GD1,fbase):
		pngfile = os.path.join(fbase+".png")
		if os.path.isfile(pngfile):
			os.remove(pngfile)
		imgx = GD1.shape[1]
		imgy = GD1.shape[0]
		# use plasma color map if available:
		try:
			plt.imshow(GD1, extent=(0, imgx, 0, imgy),cmap=cm.plasma)
			line_color = 'k'
		# else generate similar colormap
		except:
			plt.imshow(GD1, extent=(0, imgx, 0, imgy), cmap=cm.hot)
			line_color = '#009999'

		# colorbar on right
#		plt.colorbar()

		# contour lines
		X,Y = np.meshgrid(range(GD1.shape[1]),range(GD1.shape[0]))
		CS = plt.contour(X,Y[::-1],GD1,15,linewidths=0.5, colors=line_color)
		plt.clabel(CS, fontsize=9, inline=1)

		# hide x & y axis tickmarks
		plt.gca().xaxis.set_major_locator(plt.NullLocator())
		plt.gca().yaxis.set_major_locator(plt.NullLocator())

		plt.savefig(pngfile,bbox_inches='tight',pad_inches=0)
		plt.close()
		if os.path.isfile(pngfile):
			print('Writing Contour image as %s: Pass' % (pngfile,))
		else:
			print('Writing Contour image as %s: Fail' % (pngfile,))

if __name__=='__main__':
	app = TestMatPlotLib()
	app.run()
