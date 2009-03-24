#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Script to radially color a contour surface of a density map and save an
# image without starting the Chimera graphical user interface.  This uses
# the "OSMESA" version of Chimera.
#

# -----------------------------------------------------------------------------
#
import sys
import os
import time
try:
	import chimera
	from chimera.colorTable import getColorByName
	from VolumeViewer.volume import default_settings, open_volume_file
	from SurfaceColor import color_surface, Radial_Color, Color_Map, Height_Color, Cylinder_Color
	from _surface import SurfaceModel
	from chimera import openModels
	from chimera.replyobj import nogui_message
except:
	pass

class ChimSnapShots(object):
	# -----------------------------------------------------------------------------
	def renderVolume(self):
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
				self.animate_csym(h)
		else:
			if self.symmetry[:4] == 'icos':
				self.snapshot_icosahedral()
			elif self.symmetry[0] == 'd':
				self.snapshot_dsym()
			elif self.symmetry == 'c1':
				self.snapshot_asymmetric()
			else:
				self.snapshot_csym()

	# -----------------------------------------------------------------------------
	def openVolumeData(self):
		"""
		open MRC file
		set step size to 1, set contour, show surface
		create self.voldata
		"""
		default_settings.set('limit_voxel_count', False)
		default_settings.set('surface_smoothing', True)
		self.voldata = open_volume_file(self.tmpfilepath, self.fileformat)[0]
		self.voldata.set_parameters(show_outline_box=False, surface_smoothing = True, two_sided_lighting = False)
		if self.contour is not None:
			self.voldata.set_parameters(surface_levels = [self.contour])
		self.voldata.show('surface')
		self.surfaces = openModels.list(modelTypes=[SurfaceModel])
		self.setZoom()


	# -----------------------------------------------------------------------------
	def setZoom(self):
		surf = self.surfaces[0]
		vertices, triangles = surf.surfacePieces[0].geometry
		rc = Radial_Color()
		rmin, rmax = rc.value_range(vertices, vertex_xform=None)
		chimera.viewer.viewSize = rmax*1.3
		if self.zoom is not None:
			self.runChimCommand('scale %.3f' % self.zoom)

	# -----------------------------------------------------------------------------
	def color_surface_radially(self, surf, color=None):
		self.writeMessageToLog("Color radially")
		rc = Radial_Color()
		rc.origin = [0,0,0]
		vertices, triangles = surf.surfacePieces[0].geometry
		rmin, rmax = rc.value_range(vertices, vertex_xform = None)
		data_values = (.5*rmax, .625*rmax, .75*rmax, .875*rmax, rmax)
		self.writeMessageToLog("%.3f,%.3f"%(rmin,rmax))
		#key: red,green,blue,opacity
		#order: red, yellow, green, cyan, blue
		colors = [(0.9,0.1,0.1,1), (0.9,0.9,0.1,1), (0.1,0.9,0.1,1), (0.1,0.9,0.9,1), (0.1,0.1,0.9,1)]
		rc.colormap = Color_Map(data_values, colors)
		color_surface(surf, rc, caps_only = False, auto_update = False)

	# -----------------------------------------------------------------------------
	def color_surface_height(self, surf, color=None):
		self.writeMessageToLog("Color by height")
		hc = Height_Color()
		hc.origin = [0,0,0]
		vertices, triangles = surf.surfacePieces[0].geometry
		hmin, hmax = hc.value_range(vertices, vertex_xform = None)
		hrange = hmax-hmin
		#chimera.viewer.viewSize = hrange*0.9
		self.runChimCommand('scale %.3f' % self.zoom)
		self.writeMessageToLog("%.3f,%.3f"%(hmin,hmax))
		#key: red,green,blue,opacity
		#order: red, yellow, green, cyan, blue
		if color is None:
			data_values = (.125*hrange+hmin, .25*hrange+hmin, .5*hrange+hmin, .75*hrange+hmin, .875*hrange+hmin)
			colors = [(0.8,0.2,0.2,1), (0.8,0.5,0.5,1), (0.8,0.8,0.8,1), (0.5,0.5,0.8,1), (0.2,0.2,0.8,1)]
		else:
			#rgbcolor = getColorByName(color)
			colorvalues = color.split(":")
			rgbcolor = (float(colorvalues[0]), float(colorvalues[1]), float(colorvalues[2]), 1)
			print rgbcolor
			data_values = (.125*hrange+hmin, .5*hrange+hmin, .875*hrange+hmin)
			colors = [rgbcolor, (0.8,0.8,0.8,1), rgbcolor]
		hc.colormap = Color_Map(data_values, colors)
		color_surface(surf, hc, caps_only = False, auto_update = False)

	# -----------------------------------------------------------------------------
	def color_surface_cylinder(self, surf, color=None):
		self.writeMessageToLog("Color cylindrically")
		cc = Cylinder_Color()
		vertices, triangles = surf.surfacePieces[0].geometry
		cmin, cmax = cc.value_range(vertices, vertex_xform = None)
		if cmin is None:
			cmin = 0
		if cmax is None:
			cmax = 1.0
		crange = cmax - cmin
		cc.origin = [0,0,0]
		data_values = (cmin, .625*crange+cmin, .75*crange+cmin, .875*crange+cmin, cmax)
		self.writeMessageToLog("%.3f,%.3f"%(cmin,cmax))
		#key: red,green,blue,opacity
		#order: orange, yellow, green, cyan, blue
		colors = [(0.8,0.4,0.1,1), (0.8,0.8,0.1,1), (0.4,0.8,0.1,1), (0.1,0.8,0.1,1), (0.1,0.8,0.8,1)]
		cc.colormap = Color_Map(data_values, colors)
		color_surface(surf, cc, caps_only = False, auto_update = False)

	# -----------------------------------------------------------------------------
	def save_image(self, path):
		# propagate changes from C++ layer back to Python
		# can also be done via Midas module: Midas.wait(1)
		chimera.update.checkForChanges()
		# save an image
		chimera.printer.saveImage(path, format=self.imgformat)

	# -----------------------------------------------------------------------------
	def hideDust(self, size=10):
		"""
		Hide all dust particles less than 10 voxels in size
		"""
		try:
			from HideDust import dust
			self.writeMessageToLog("hiding dust of size %.1f"%(size))
			#writeMessageToLog(str(dir(dust))
			#writeMessageToLog(str(help(dust))
			dust.hide_dust(self.voldata, 'size', size, auto_update=True)
			#runChimCommand('hide dust # %d'%(size))
		except:
			self.writeMessageToLog("skipping hide dust")
			pass


	# -----------------------------------------------------------------------------
	def animate_icosahedral(self):
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_radially(s, self.color)
		self.save_image(self.volumepath+'.001.png')
		self.writeMessageToLog("turn: down 3-fold axis")
		self.runChimCommand('turn y 37.377')
		self.save_image(self.volumepath+'.002.png')
		self.writeMessageToLog("turn: viper orientation (2 fold)")
		self.runChimCommand('turn y 20.906')
		self.save_image(self.volumepath+'.003.png')
		self.writeMessageToLog("turn: get clipped view")
		time.sleep(0.5)
		self.runChimCommand('mclip #0 coords screen axis z')
		self.runChimCommand('wait')
		time.sleep(0.5)
		self.runChimCommand('ac cc')
		self.runChimCommand('wait')
		time.sleep(0.5)
		self.save_image(self.volumepath+'.006.png')

	# -----------------------------------------------------------------------------
	def animate_asymmetric(self):
		self.hideDust(50)
		for s in self.surfaces:
			self.color_surface_height(s, self.color)
		self.writeMessageToLog("turn: get top view")
		self.runChimCommand("turn x 180")
		tilt = 15
		self.runChimCommand("turn x %d"%(-tilt))
		increment = 4
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
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_cylinder(s, self.color)
		self.writeMessageToLog("turn: get intermediate side view")
		self.runChimCommand('turn x 90')
		tilt = 30
		self.runChimCommand("turn x %d"%(tilt))
		increment = 5
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
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_height(s, self.color)
		self.writeMessageToLog("turn: get intermediate side view")
		self.runChimCommand('turn x 90')
		tilt = 30
		self.runChimCommand("turn x %d"%(tilt))
		increment = 15
		nsteps = int(180/increment)
		for i in range(nsteps):
			self.filename = "%s.%03d.%s"%(self.volumepath, i, self.imgformat.lower())
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
		image1 = self.volumepath+'.1.png'
		image2 = self.volumepath+'.2.png'
		image3 = self.volumepath+'.3.png'
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_radially(s, self.color)
		self.save_image(self.volumepath+'.1.png')
		self.writeMessageToLog("turn: down 3-fold axis")
		self.runChimCommand('turn y 37.377')
		self.save_image(self.volumepath+'.2.png')
		self.writeMessageToLog("turn: viper orientation (2 fold)")
		self.runChimCommand('turn y 20.906')
		self.save_image(self.volumepath+'.3.png')
		self.writeMessageToLog("turn: get clipped view")
		time.sleep(0.5)
		self.runChimCommand('mclip #0 coords screen axis z')
		self.runChimCommand('wait')
		time.sleep(0.5)
		self.runChimCommand('ac cc')
		self.runChimCommand('wait')
		time.sleep(0.5)
		self.save_image(self.volumepath+'.6.png')

	# -----------------------------------------------------------------------------
	def snapshot_asymmetric(self):
		self.hideDust(50)
		for s in self.surfaces:
			self.color_surface_height(s, self.color)
		self.writeMessageToLog("turn: get front view")
		self.runChimCommand('turn x 180')
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
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_cylinder(s, self.color)
		self.writeMessageToLog("turn: get top view")
		self.runChimCommand('turn x 180')
		self.save_image(self.volumepath+'.1.png')
		self.writeMessageToLog("turn: get tilt view")
		self.runChimCommand('turn x -45')
		self.save_image(self.volumepath+'.2.png')
		self.writeMessageToLog("turn: get side view")
		self.runChimCommand('turn x -45')
		self.save_image(self.volumepath+'.3.png')

	# -----------------------------------------------------------------------------
	def snapshot_csym(self):
		self.hideDust(10)
		for s in self.surfaces:
			self.color_surface_cylinder(s, self.color)
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
		self.chimlog = os.path.join(self.rundir, "chimera.log")
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
		self.color = os.environ.get('CHIMCOLOR')
		### Silhouette
		silhouette = os.environ.get('CHIMSILHOUETTE')
		if silhouette is not None and bool(silhouette) is True:
			chimera.viewer.showSilhouette = True
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
			self.imgsize = (imgsize, imgsize)
		elif self.type == 'animate':
			self.imgsize = (128,128)
		else:
			self.imgsize = (1024,1024)
		### file format
		self.fileformat = os.environ.get('CHIMFILEFORMAT')
		if self.fileformat is None:
			self.fileformat = "mrc"
		### write to log
		variables = (
			'CHIMVOL', 'CHIMTEMPVOL', 'CHIMSYM', 'CHIMCONTOUR', 'CHIMCOLOR',
			'CHIMTYPE', 'CHIMSILHOUETTE', 'CHIMBACK', 'CHIMZOOM', 'CHIMIMGSIZE',
			'CHIMIMGFORMAT', 'CHIMFILEFORMAT',
		)
		self.writeMessageToLog("Environmental data: ")
		for var in variables:
			self.writeMessageToLog("%s: %s"%(var, os.environ.get(var)))

#==========================================
#==========================================
#==========================================

if True:
	chim = ChimSnapShots()
	chim.renderVolume()

	chimera.ChimeraExit()
	chimera.ChimeraSystemExit()
	sys.exit(1)






