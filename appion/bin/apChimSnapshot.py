#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Script to radially color a contour surface of a density map and save an
# image without starting the Chimera graphical user interface.  This uses
# the "OSMESA" version of Chimera.
#

# -----------------------------------------------------------------------------
#
import sys
import re
import os
import time
import numpy
import math

### fail if not run from within chimera
if __name__ == "__main__":
	sys.stderr.write("\nusage: chimera python:apChimSnapshot.py\n\n")
	sys.exit(1)
try:
	import chimera
	import chimera.printer
	from chimera.colorTable import getColorByName
	from VolumeViewer.volume import default_settings, open_volume_file
	import Surface
	from SurfaceColor import color_surface, Radial_Color, Color_Map, Height_Color, Cylinder_Color
	from SurfaceCap import surfcaps
	from _surface import SurfaceModel, connected_pieces
	from chimera import openModels
	from chimera.replyobj import nogui_message
	from MeasureVolume import enclosed_volume
	import ScaleBar.session
except:
	pass

class ChimSnapShots(object):
	# -----------------------------------------------------------------------------
	def renderVolume(self):
		self.writeMessageToLog("rendering volume")
		chimera.viewer.windowSize = self.imgsize
		self.openVolumeData()

		### select proper function
		if self.type == 'animate':
			if self.symmetry[:4] == 'icos':
				self.animate_icosahedral()
			elif self.symmetry[0] == 'd':
				self.animate_dsym()
			elif self.symmetry == 'c1':
				self.animate_asymmetric()
			else:
				self.animate_csym()
		else:
			if self.symmetry[:4] == 'icos':
				self.snapshot_icosahedral()
			elif self.symmetry == 'oct':
				self.snapshot_octahedral()
			elif self.symmetry[0] == 'd':
				self.snapshot_dsym()
			elif self.symmetry[:4] == 'ribo':
				self.snapshot_ribosome()
			elif self.symmetry == 'c1':
				self.snapshot_asymmetric()
			else:
				self.snapshot_csym()

		self.saveChimeraState()

		self.writeMessageToLog("\n")
		self.writeMessageToLog("====================================")
		self.writeMessageToLog("apChimSnapshot finished successfully")
		self.writeMessageToLog("====================================")
		self.writeMessageToLog("\n\n\n")

	# -----------------------------------------------------------------------------
	def saveChimeraState(self):
		from SimpleSession.save import saveSession
		self.sessionname = re.sub("\.", "_", self.volumepath)+".py"
		self.writeMessageToLog("Saving chimera session: %s"%(self.sessionname))
		saveSession(self.sessionname)
		if os.path.isfile(self.sessionname):
			self.writeMessageToLog("SUCCESS Saving chimera session")
		else:
			self.writeMessageToLog("FAIL Saving chimera session")
		return


	# -----------------------------------------------------------------------------
	def openVolumeData(self):
		"""
		open MRC file
		set step size to 1, set contour, show surface
		create self.voldata
		"""
		self.writeMessageToLog("Opening volume type: %s file: %s"%(self.fileformat, self.tmpfilepath))
		default_settings.set('limit_voxel_count', False)
		default_settings.set('surface_smoothing', True)
		default_settings.set('smoothing_iterations', 10)
		self.voldata = open_volume_file(self.tmpfilepath, self.fileformat)[0]
		#self.writeMessageToLog(str(dir(self.voldata)))
		self.voldata.set_parameters(
			show_outline_box=False,
			surface_smoothing=True,
			two_sided_lighting=False,
		)
		if self.contour is not None:
			self.voldata.set_parameters(surface_levels = [self.contour])
		self.voldata.show('surface')
		self.surfaces = openModels.list(modelTypes=[SurfaceModel])
		self.setZoom()

		### This does not work on CentOS and Chimera v1.2509, but does with Chimera v1.4
		if float((chimera.version.release).split('_')[0]) > 1.3:
			### draw scale bar if version greater than 1.3
			self.drawScaleBar()
		else:
			self.writeMessageToLog("Skipping scale bar")

	# -----------------------------------------------------------------------------
	def setZoom(self):
		self.writeMessageToLog("Setting zoom")
		surf = self.surfaces[0]
		rc = Radial_Color()
		try:
			rmin, rmax = rc.value_range(surf.surfacePieces[0])
		except:
			#keep for older version of chimera, e.g. v1.2509
			vertices, triangles = surf.surfacePieces[0].geometry
			rmin, rmax = rc.value_range(vertices, vertex_xform=None)
		while rmax is None:
			self.writeMessageToLog("Contour %.2f is too big, no surface is shown"%(self.contour))
			self.contour *= 0.9
			self.voldata.set_parameters(surface_levels = [self.contour])
			self.voldata.show('surface')
			self.surfaces = openModels.list(modelTypes=[SurfaceModel])
			surf = self.surfaces[0]
			try:
				rmin, rmax = rc.value_range(surf.surfacePieces[0])
			except:
				#keep for older version of chimera, e.g. v1.2509
				vertices, triangles = surf.surfacePieces[0].geometry
				rmin, rmax = rc.value_range(vertices, vertex_xform=None)
		## ten percent bigger to ensure that entire particle is in frame
		chimera.viewer.viewSize = 1.1*rmax/self.zoom
		#self.runChimCommand('scale %.3f' % self.zoom)

	# -----------------------------------------------------------------------------
	def getColors(self):
			### set colors
		if len(self.colors) >= 1 and ":" in self.colors[0]:
			colorvalues = self.colors[0].split(":")
			rgbcolor0 = (float(colorvalues[0]), float(colorvalues[1]), float(colorvalues[2]), 1)
		else:
			rgbcolor0 = (0.8,0.2,0.2,1)
		if len(self.colors) >= 2 and ":" in self.colors[1]:
			colorvalues = self.colors[1].split(":")
			rgbcolor1 = (float(colorvalues[0]), float(colorvalues[1]), float(colorvalues[2]), 1)

		else:
			rgbcolor1 = (0.8,0.8,0.8,1)
		if len(self.colors) >= 3 and ":" in self.colors[2]:
			colorvalues = self.colors[2].split(":")
			rgbcolor2 = (float(colorvalues[0]), float(colorvalues[1]), float(colorvalues[2]), 1)
		else:
			rgbcolor2 = (0.2,0.2,0.8,1)
		self.writeMessageToLog("rgbcolor0 = %.1f, %.1f, %.1f, %.1f"%(rgbcolor0))
		self.writeMessageToLog("rgbcolor1 = %.1f, %.1f, %.1f, %.1f"%(rgbcolor1))
		self.writeMessageToLog("rgbcolor2 = %.1f, %.1f, %.1f, %.1f"%(rgbcolor2))
		colors = [rgbcolor0, rgbcolor1, rgbcolor2]
		return colors

	# -----------------------------------------------------------------------------
	def color_surface_radially(self, surf):
		self.writeMessageToLog("Color radially")
		rc = Radial_Color()
		rc.origin = [0,0,0]
		try:
			rmin, rmax = rc.value_range(surf.surfacePieces[0])
		except:
			#keep for older version of chimera, e.g. v1.2509
			vertices, triangles = surf.surfacePieces[0].geometry
			rmin, rmax = rc.value_range(vertices, vertex_xform=None)
		rrange = rmax-rmin
		self.writeMessageToLog("%.3f,%.3f"%(rmin,rmax))
		#key: red,green,blue,opacity
		#order: red, yellow, green, cyan, blue
		if self.colors is None:
			data_values = (.5*rmax, .625*rmax, .75*rmax, .875*rmax, rmax)
			colors = [(0.9,0.1,0.1,1), (0.9,0.9,0.1,1), (0.1,0.9,0.1,1), (0.1,0.9,0.9,1), (0.1,0.1,0.9,1)]
		else:
			### set colors
			colors = self.getColors()
			data_values = (.125*rrange+rmin, .5*rrange+rmin, .875*rrange+rmin)
		rc.colormap = Color_Map(data_values, colors)
		color_surface(surf, rc, caps_only = False, auto_update = False)

	# -----------------------------------------------------------------------------
	def color_surface_height(self, surf):
		self.writeMessageToLog("Color by height")
		hc = Height_Color()
		hc.origin = [0,0,0]
		try:
			hmin, hmax = hc.value_range(surf.surfacePieces[0])
		except:
			#keep for older version of chimera, e.g. v1.2509
			vertices, triangles = surf.surfacePieces[0].geometry
			hmin, hmax = hc.value_range(vertices, vertex_xform=None)
		hrange = hmax-hmin
		self.writeMessageToLog("%.3f,%.3f"%(hmin,hmax))
		#key: red,green,blue,opacity
		if self.colors is None:
			### red, white blue
			data_values = (.125*hrange+hmin, .25*hrange+hmin, .5*hrange+hmin, .75*hrange+hmin, .875*hrange+hmin)
			colors = [(0.8,0.2,0.2,1), (0.8,0.5,0.5,1), (0.8,0.8,0.8,1), (0.5,0.5,0.8,1), (0.2,0.2,0.8,1)]
		else:
			### set colors
			colors = self.getColors()
			data_values = (.125*hrange+hmin, .5*hrange+hmin, .875*hrange+hmin)
		hc.colormap = Color_Map(data_values, colors)
		color_surface(surf, hc, caps_only = False, auto_update = False)

	# -----------------------------------------------------------------------------
	def color_surface_cylinder(self, surf):
		self.writeMessageToLog("Color cylindrically")
		cc = Cylinder_Color()
		try:
			cmin, cmax = rc.value_range(surf.surfacePieces[0])
		except:
			#keep for older version of chimera, e.g. v1.2509
			vertices, triangles = surf.surfacePieces[0].geometry
			cmin, cmax = cc.value_range(vertices, vertex_xform=None)
		if cmin is None:
			cmin = 0
		if cmax is None:
			cmax = 1.0
		crange = cmax - cmin
		cc.origin = [0,0,0]
		self.writeMessageToLog("%.3f,%.3f"%(cmin,cmax))
		if self.colors is None:
			### green, yellow, orange
			data_values = (cmin, .625*crange+cmin, .75*crange+cmin, .875*crange+cmin, cmax)
			#key: red,green,blue,opacity
			#order: orange, yellow, green, cyan, blue
			colors = [(0.8,0.4,0.1,1), (0.8,0.8,0.1,1), (0.4,0.8,0.1,1), (0.1,0.8,0.1,1), (0.1,0.8,0.8,1)]
		else:
			### set colors
			colors = self.getColors()
			data_values = (.125*crange+cmin, .5*crange+cmin, .875*crange+cmin)
		cc.colormap = Color_Map(data_values, colors)
		color_surface(surf, cc, caps_only = False, auto_update = False)

	# -----------------------------------------------------------------------------
	def save_image(self, path):
		self.writeMessageToLog("Saving image: "+path)
		# propagate changes from C++ layer back to Python
		# can also be done via Midas module: Midas.wait(1)

		# save an image
		chimera.printer.saveImage(path, format=self.imgformat)
		if os.path.isfile(path):
			self.writeMessageToLog("Success, saved image: "+path)
		else:
			self.writeMessageToLog("FAILED to save image: "+path)

	# -----------------------------------------------------------------------------
	def drawScaleBar(self, size=50):
		self.writeMessageToLog("Draw a scale bar %d Angstroms long"%(size))
		try:
			scale_bar_state = {
				'bar_length': str(size),
				'bar_rgba': ( 0.0, 0.0, 0.0, 1.0,),
				'bar_thickness': '1',
				'class': 'Scale_Bar_Dialog_State',
				'frozen_models': [ ],
				'geometry': '%dx%d+3+3'%(self.imgsize[0]/2, self.imgsize[1]/2),
				'is_visible': False,
				'label_rgba': ( 0.0, 0.0, 0.0, 1.0,),
				'label_text': '# A',
				'label_x_offset': '-3',
				'label_y_offset': '3',
				'model': {},
				'move_scalebar': 0,
				'orientation': 'horizontal',
				'preserve_position': False,
				'screen_x_position': '-0.6',
				'screen_y_position': '-0.9',
				'show_scalebar': True,
				'version': 1,
			}
			ScaleBar.session.restore_scale_bar_state(scale_bar_state)
		except:
			self.writeMessageToLog("Error restoring scale bar")

	# -----------------------------------------------------------------------------
	def hideDust(self, size=100):
		self.writeMessageToLog("Hide all dust particles less than %d voxels in size"%(size))
		native = False
		#try:
		if True:
			if native is True:
				from HideDust import dust
				self.writeMessageToLog("hiding dust of size %.1f"%(size))
				#writeMessageToLog(str(dir(dust))
				#writeMessageToLog(str(help(dust))
				dust.hide_dust(self.voldata, 'size', size, auto_update=True)
				#runChimCommand('hide dust # %d'%(size))
			else:
				for surf in self.selected_surface_pieces():
					self.hide_small_blobs(surf, size)
		if False:
		#except:
			self.writeMessageToLog("skipping hide dust")
			pass

	# -----------------------------------------------------------------------------
	def hide_small_blobs(self, surf, size=100):
		varray, tarray = surf.geometry
		mask = numpy.ones((len(varray),), numpy.intc)
		cplist = connected_pieces(tarray)
		hid = 0
		for vi, ti in cplist:
			ta = tarray.take(ti, axis = 0)
			vol, holes = enclosed_volume(varray, ta)
			if not vol is None and vol < size:
				mask.put(vi, 0)
				hid += 1
		surf.setTriangleMaskFromVertexMask(mask)
		self.writeMessageToLog("Hid %d of %d connected surface components having volume < %.1f"
			% (hid, len(cplist), size))

	# -----------------------------------------------------------------------------
	def selected_surface_pieces(self):
		plist = Surface.selected_surface_pieces()
		if len(plist) > 0:
			return plist
		plist = []
		for m in openModels.list(modelTypes = [SurfaceModel]):
			plist.extend(m.surfacePieces)
		return plist

	# -----------------------------------------------------------------------------
	def animate_icosahedral(self):
		self.writeMessageToLog("animate_icosahedral")
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_radially(s)
		stepsize = 15.0
		numpause = 3

		### pause
		imgnum = 0
		for i in range(numpause):
			imgnum += 1
			filename = "%s.%03d.%s"%(self.volumepath, imgnum, self.imgformat.lower())
			self.save_image(filename)

		### down 3-fold axis
		self.writeMessageToLog("turn: down 3-fold axis")
		threefoldangle = 37.377
		threefoldsteps = int(threefoldangle/stepsize)+1
		threefoldstepangle = threefoldangle/float(threefoldsteps)
		for i in range(threefoldsteps):
			imgnum += 1
			filename = "%s.%03d.%s"%(self.volumepath, imgnum, self.imgformat.lower())
			self.runChimCommand('turn y %.4f'%(threefoldstepangle))
			self.save_image(filename)
	
		### pause
		for i in range(numpause):
			imgnum += 1
			filename = "%s.%03d.%s"%(self.volumepath, imgnum, self.imgformat.lower())
			self.save_image(filename)

		### viper orientation (2 fold)
		self.writeMessageToLog("turn: viper orientation (2 fold)")
		viperangle = 20.906
		vipersteps = int(viperangle/stepsize)+1
		viperstepangle = viperangle/float(vipersteps)
		for i in range(vipersteps):
			imgnum += 1
			filename = "%s.%03d.%s"%(self.volumepath, imgnum, self.imgformat.lower())
			self.runChimCommand('turn y %.4f'%(viperstepangle))
			self.save_image(filename)

		### pause
		for i in range(numpause):
			imgnum += 1
			filename = "%s.%03d.%s"%(self.volumepath, imgnum, self.imgformat.lower())
			self.save_image(filename)

		### clip
		#self.writeMessageToLog("turn: get clipped view")
		#self.runChimCommand('mclip #0 coords screen axis z')
		#self.runChimCommand('wait')
		#self.runChimCommand('ac cc')
		#self.runChimCommand('wait')

		### pause
		for i in range(numpause):
			imgnum += 1
			filename = "%s.%03d.%s"%(self.volumepath, imgnum, self.imgformat.lower())
			self.save_image(filename)

		### walk back
		### viper orientation (2 fold)
		self.writeMessageToLog("turn: viper orientation (2 fold)")
		for i in range(vipersteps):
			imgnum += 1
			filename = "%s.%03d.%s"%(self.volumepath, imgnum, self.imgformat.lower())
			self.runChimCommand('turn y %.4f'%(-viperstepangle))
			self.save_image(filename)

		### pause
		for i in range(numpause):
			imgnum += 1
			filename = "%s.%03d.%s"%(self.volumepath, imgnum, self.imgformat.lower())
			self.save_image(filename)

		### down 3-fold axis
		self.writeMessageToLog("turn: down 3-fold axis")
		for i in range(threefoldsteps):
			imgnum += 1
			filename = "%s.%03d.%s"%(self.volumepath, imgnum, self.imgformat.lower())
			self.runChimCommand('turn y %.4f'%(-threefoldstepangle))
			self.save_image(filename)

	# -----------------------------------------------------------------------------
	def animate_asymmetric(self):
		self.writeMessageToLog("animate_asymmetric")
		self.hideDust(250)
		for s in self.surfaces:
			self.color_surface_height(s)
		#self.writeMessageToLog("turn: get top view")
		#self.runChimCommand("turn x 180")
		tilt = 15
		self.runChimCommand("turn x %d"%(-tilt))
		increment = 20
		nsteps = int(360/increment)
		for i in range(nsteps):
			filename = "%s.%03d.%s"%(self.volumepath, i, self.imgformat.lower())
			self.save_image(filename)
			self.writeMessageToLog("turn: rotate by %d to %d"%(increment,increment*(i+1)))
			self.runChimCommand("turn x %d"%(tilt))
			self.runChimCommand("turn y %d"%(increment))
			self.runChimCommand("turn x %d"%(-tilt))
		for i in range(nsteps):
			filename = "%s.%03d.%s"%(self.volumepath, i+nsteps, self.imgformat.lower())
			self.save_image(filename)
			self.writeMessageToLog("turn: rotate by %d to %d"%(increment,increment*(i+1)))
			self.runChimCommand("turn x %d"%(increment))

	# -----------------------------------------------------------------------------
	def animate_dsym(self):
		self.writeMessageToLog("animate_dsym")
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_cylinder(s)
		self.writeMessageToLog("turn: get intermediate side view")
		self.runChimCommand('turn x 90')
		tilt = 30
		self.runChimCommand("turn x %d"%(tilt))
		increment = 10
		nsteps = int(360/increment)
		for i in range(nsteps):
			filename = "%s.%03d.%s"%(self.volumepath, i, self.imgformat.lower())
			self.save_image(filename)
			self.writeMessageToLog("turn: rotate by %d to %d"%(increment,increment*(i+1)))
			self.runChimCommand("turn x %d"%(-tilt))
			self.runChimCommand("turn y %d"%(increment))
			self.runChimCommand("turn x %d"%(tilt))

	# -----------------------------------------------------------------------------
	def animate_csym(self):
		self.writeMessageToLog("animate_csym")
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_height(s)
		self.writeMessageToLog("turn: get intermediate side view")
		self.runChimCommand('turn x 90')
		tilt = 30
		self.runChimCommand("turn x %d"%(tilt))
		increment = 30
		nsteps = int(180/increment)
		for i in range(nsteps):
			filename = "%s.%03d.%s"%(self.volumepath, i, self.imgformat.lower())
			self.save_image(filename)
			self.writeMessageToLog("turn: rotate about by %d to %d"%(increment,increment*(i+1)))
			self.runChimCommand("turn x %d"%(-tilt))
			self.runChimCommand("turn y %d"%(increment))
			self.runChimCommand("turn x %d"%(tilt))
		for i in range(nsteps):
			filename = "%s.%03d.%s"%(self.volumepath, i+nsteps, self.imgformat.lower())
			self.save_image(filename)
			self.writeMessageToLog("turn: rotate down by %d to %d"%(increment,increment*(i+1)))
			self.runChimCommand("turn x %d"%(increment))
		for i in range(nsteps):
			filename = "%s.%03d.%s"%(self.volumepath, i+nsteps*2, self.imgformat.lower())
			self.save_image(filename)
			self.writeMessageToLog("turn: rotate about by %d to %d"%(increment,increment*(i+1)))
			self.runChimCommand("turn x %d"%(-tilt))
			self.runChimCommand("turn y %d"%(increment))
			self.runChimCommand("turn x %d"%(tilt))
		for i in range(nsteps):
			filename = "%s.%03d.%s"%(self.volumepath, i+nsteps*3, self.imgformat.lower())
			self.save_image(filename)
			self.writeMessageToLog("turn: rotate up by %d to %d"%(increment,increment*(i+1)))
			self.runChimCommand("turn x %d"%(-increment))

	# -----------------------------------------------------------------------------
	def snapshot_icosahedral(self):
		self.writeMessageToLog("snapshot_icosahedral")
		image1 = self.volumepath+'.1.png'
		image2 = self.volumepath+'.2.png'
		image3 = self.volumepath+'.3.png'
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_radially(s)
		self.save_image(self.volumepath+'.1.png')
		self.writeMessageToLog("turn: down 3-fold axis")
		self.runChimCommand('turn y 37.377')
		self.save_image(self.volumepath+'.2.png')
		self.writeMessageToLog("turn: viper orientation (2 fold)")
		self.runChimCommand('turn y 20.906')
		self.save_image(self.volumepath+'.3.png')
		self.writeMessageToLog("turn: get clipped view")

		### add clipping plane
		self.runChimCommand('mclip #0 coords screen axis z')
		self.runChimCommand('ac cc')
		#self.capper = surfcaps.Surface_Capper()
		#self.capper.show_caps()
		#self.capper.unshow_caps()

		self.save_image(self.volumepath+'.6.png')

	# -----------------------------------------------------------------------------
	def snapshot_octahedral(self):
		self.writeMessageToLog("snapshot_octahedral")
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_radially(s)
		self.save_image(self.volumepath+'.1.png')
		self.writeMessageToLog("turn: down 2-fold axis")
		# 45 degrees is 1/8 turn to get side of cube
		self.runChimCommand('turn y 45.0')
		self.save_image(self.volumepath+'.2.png')
		self.writeMessageToLog("turn: down 3-fold axis")
		# arctan(sqrt(2)/2) = 35.26 degrees turn to get corner of cube
		angle = math.degrees(math.atan2(math.sqrt(2.),2.))
		self.runChimCommand('turn x %.5f'%(angle))
		self.save_image(self.volumepath+'.3.png')
		self.writeMessageToLog("turn: get clipped view")

		### add clipping plane
		self.runChimCommand('mclip #0 coords screen axis z')
		self.runChimCommand('ac cc')
		#self.capper = surfcaps.Surface_Capper()
		#self.capper.show_caps()
		#self.capper.unshow_caps()

		self.save_image(self.volumepath+'.4.png')

	# -----------------------------------------------------------------------------
	def snapshot_ribosome(self):
		self.writeMessageToLog("snapshot_ribosome")
		self.hideDust(150)
		for s in self.surfaces:
			self.color_surface_height(s)
		self.writeMessageToLog("turn: get top view")
		self.runChimCommand('turn x +45')
		self.save_image(self.volumepath+'.1.png')
		self.writeMessageToLog("turn: back to front view")
		self.runChimCommand('turn x -45')
		self.save_image(self.volumepath+'.2.png')
		self.writeMessageToLog("turn: get side view")
		self.runChimCommand('turn y -60')
		self.save_image(self.volumepath+'.3.png')

	# -----------------------------------------------------------------------------
	def snapshot_asymmetric(self):
		self.writeMessageToLog("snapshot_asymmetric")
		self.hideDust(150)
		for s in self.surfaces:
			self.color_surface_height(s)
		#self.writeMessageToLog("turn: get front view")
		#self.runChimCommand('turn x 180')
		self.save_image(self.volumepath+'.1.png')
		self.writeMessageToLog("turn: get front 60 tilt view")
		self.runChimCommand('turn y -60')
		self.save_image(self.volumepath+'.2.png')
		self.writeMessageToLog("turn: get front 120 tilt view")
		self.runChimCommand('turn y -60')
		self.save_image(self.volumepath+'.3.png')
		self.writeMessageToLog("turn: get back view")
		self.runChimCommand('turn y -60')
		self.save_image(self.volumepath+'.4.png')
		self.writeMessageToLog("turn: get back 60 tilt view")
		self.runChimCommand('turn y -60')
		self.save_image(self.volumepath+'.5.png')
		self.writeMessageToLog("turn: get back 120 tilt view")
		self.runChimCommand('turn y -60')
		self.save_image(self.volumepath+'.6.png')

	# -----------------------------------------------------------------------------
	def snapshot_dsym(self):
		self.writeMessageToLog("snapshot_dsym")
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_cylinder(s)
		self.writeMessageToLog("turn: get top view")
		self.runChimCommand('turn x 180')
		self.save_image(self.volumepath+'.1.png')

		"""
		### hack
		self.runChimCommand('turn x -30')	
		self.save_image(self.volumepath+'.30deg1.png')
		self.runChimCommand('turn y 20')
		self.save_image(self.volumepath+'.30deg2.png')

		### unhack
		self.runChimCommand('turn y -20')
		self.runChimCommand('turn x 30')
		"""

		### resume
		self.writeMessageToLog("turn: get tilt view")
		self.runChimCommand('turn x -45')
		self.save_image(self.volumepath+'.2.png')
		self.writeMessageToLog("turn: get side view")
		self.runChimCommand('turn x -45')
		self.save_image(self.volumepath+'.3.png')
		dfold = int(self.symmetry[1:])
		dangle = 180.0/dfold
		self.writeMessageToLog("turn about dsym: %.3f"%(dangle))
		self.runChimCommand('turn y %.3f'%(dangle))
		self.save_image(self.volumepath+'.4.png')

	# -----------------------------------------------------------------------------
	def snapshot_csym(self):
		self.writeMessageToLog("snapshot_csym")
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_height(s)
		self.writeMessageToLog("turn: get top view")
		self.runChimCommand('turn x 180')
		self.save_image(self.volumepath+'.1.png')
		self.writeMessageToLog("turn: get tilt view")
		self.runChimCommand('turn x -45')
		self.save_image(self.volumepath+'.2.png')
		self.writeMessageToLog("turn: get side view")
		self.runChimCommand('turn x -45')
		self.save_image(self.volumepath+'.3.png')
		self.writeMessageToLog("turn: get tilt 2")
		self.runChimCommand('turn x -45')
		self.save_image(self.volumepath+'.4.png')
		self.writeMessageToLog("turn: bottom view")
		self.runChimCommand('turn x -45')
		self.save_image(self.volumepath+'.5.png')

	# -----------------------------------------------------------------------------
	def runChimCommand(self, cmd):
		if self.chimlog is not None:
			f = open(self.chimlog, "a")
			f.write(str(cmd)+"\n")
			f.close()
			#nogui_message(cmd.strip()+"\n")
		chimera.runCommand(cmd)

	# -----------------------------------------------------------------------------
	def writeMessageToLog(self, msg):
		if self.chimlog is None:
			return
		f = open(self.chimlog, "a")
		f.write(str(msg)+"\n")
		#nogui_message(msg.strip()+"\n")
		f.close()

	# -----------------------------------------------------------------------------
	def message(self, m):
		""" Print status message. """
		nogui_message(m + '\n')

	# -----------------------------------------------------------------------------
	def valueToBool(self, val):
		if val is None:
			return False
		if val == "":
			return False
		if val == 0:
			return False
		if val.lower() == "f":
			return False
		if val.lower() == "false":
			return False
		return True

	# -----------------------------------------------------------------------------
	def __init__(self):
		### Volume name
		self.volumepath = os.environ.get('CHIMVOL')
		print self.volumepath
		if self.volumepath is None:
			sys.exit(1)
		self.rundir = os.path.dirname(self.volumepath)
		self.chimlog = os.path.join(self.rundir, "apChimSnapshot.log")

		self.writeMessageToLog("\n\n")
		self.writeMessageToLog("======================")
		self.writeMessageToLog("Running apChimSnapshot")
		self.writeMessageToLog("======================")
		self.writeMessageToLog("\n")

		### Temporary volume, low pass filtered
		self.tmpfilepath = os.environ.get('CHIMTEMPVOL')
		if self.tmpfilepath is None:
			self.tmpfilepath = self.volumepath
		### Symmetry
		self.symmetry = os.environ.get('CHIMSYM')
		if self.symmetry is None:
			self.symmetry = 'c1'
		else:
			self.symmetry = self.symmetry.lower()
		### Zoom factor
		self.zoom = os.environ.get('CHIMZOOM')
		if self.zoom is None:
			self.zoom = 1.0
		else:
			self.zoom = float(self.zoom)
		### Contour factor
		self.contour = os.environ.get('CHIMCONTOUR')
		if self.contour is not None:
			self.contour = float(self.contour)
		### Image type
		self.type = os.environ.get('CHIMTYPE')
		if self.type is None or self.type not in ('snapshot', 'animate'):
			self.type = 'snapshot'
		### Color array
		colors = os.environ.get('CHIMCOLORS')
		if colors is not None and "," in colors:
			self.colors = colors.split(",")
		else:
			self.colors = None
		### Silhouette
		silhouette = os.environ.get('CHIMSILHOUETTE')
		if silhouette is not None and bool(silhouette) is True:
			chimera.viewer.showSilhouette = True
			chimera.viewer.silhouetteWidth = 3.0
		elif silhouette is None or bool(silhouette) is False:
			chimera.viewer.showSilhouette = False
		### Background
		if os.environ.get('CHIMBACK') is None:
			white = getColorByName('white')
			chimera.viewer.background = white
		else:
			backcolor = os.environ.get('CHIMBACK').strip()
			color = getColorByName(backcolor)
			chimera.viewer.background = color
		### image format
		self.imgformat = os.environ.get('CHIMIMGFORMAT')
		if self.imgformat is None:
			self.imgformat = "PNG"
		### image size
		imgsize = os.environ.get('CHIMIMGSIZE')
		if imgsize is not None:
			imgsize = int(imgsize)
			self.imgsize = (imgsize, imgsize)
		elif self.type == 'animate':
			self.imgsize = (256,256)
		else:
			self.imgsize = (1024,1024)
		### file format
		self.fileformat = os.environ.get('CHIMFILEFORMAT')
		if self.fileformat is None:
			self.fileformat = "mrc"
		### write to log
		self.writeMessageToLog("Chimera version: %s"%(chimera.version.version))
		self.writeMessageToLog("Environmental data: ")
		for var in os.environ.keys():
			if var[:4] == "CHIM":
				if os.environ.get(var) is not None:
					self.writeMessageToLog("export %s=%s"%(var, os.environ.get(var)))		

#==========================================
#==========================================
#==========================================

if True:
	chim = ChimSnapShots()
	chim.renderVolume()
	chimera.ChimeraExit()
	chimera.ChimeraSystemExit()
	sys.exit(1)






