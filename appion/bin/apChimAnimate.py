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
import chimera
import time

chimlog=None

def openVolumeData(vpath, file_type="mrc", contour_level=1.5, color=None):

	# set step size to 1
	from VolumeViewer.volume import default_settings
	default_settings.set('limit_voxel_count', False)

	from VolumeViewer import open_volume_file
	v = open_volume_file(vpath, file_type)[0]

	v.set_parameters(show_outline_box = False, surface_smoothing = True, two_sided_lighting = False)

	if contour_level is not None:
		v.set_parameters(surface_levels = [contour_level])
	if color is not None:
		v.set_parameters(surface_colors = [color])

	v.show('surface')

	return v

# -----------------------------------------------------------------------------
# Print status message.
#

def message(m):

	from chimera.replyobj import nogui_message
	nogui_message(m + '\n')

# -----------------------------------------------------------------------------
#
def color_surface_radially(surf):
	writeMessageToLog("Color radially")
	from SurfaceColor import color_surface, Radial_Color, Color_Map
	rc = Radial_Color()
	rc.origin = [0,0,0]
	vertices, triangles = surf.surfacePieces[0].geometry
	rmin, rmax = rc.value_range(vertices, vertex_xform = None)
	data_values = (.5*rmax, .625*rmax, .75*rmax, .875*rmax, rmax)
	writeMessageToLog("%.3f,%.3f"%(rmin,rmax))
	#key: red,green,blue,opacity
	#order: red, yellow, green, cyan, blue
	colors = [(0.933,0.067,0.067,1), (0.933,0.933,0.067,1), (0.067,0.933,0.067,1), (0.067,0.933,0.933,1), (0.067,0.067,0.933,1)]  

	rc.colormap = Color_Map(data_values, colors)
	color_surface(surf, rc, caps_only = False, auto_update = False)

# -----------------------------------------------------------------------------
#
def color_surface_height(surf):
	writeMessageToLog("Color by height")
	from SurfaceColor import color_surface, Height_Color, Color_Map
	hc = Height_Color()
	hc.origin = [0,0,0]
	vertices, triangles = surf.surfacePieces[0].geometry
	hmin, hmax = hc.value_range(vertices, vertex_xform = None)
	hrange = hmax-hmin
	data_values = (.125*hrange+hmin, .25*hrange+hmin, .5*hrange+hmin, .75*hrange+hmin, .875*hrange+hmin)
	writeMessageToLog("%.3f,%.3f"%(hmin,hmax))
	#key: red,green,blue,opacity
	#order: red, yellow, green, cyan, blue
	colors = [(0.8,0.2,0.2,1), (0.8,0.5,0.5,1), (0.8,0.8,0.8,1), (0.5,0.5,0.8,1), (0.2,0.2,0.8,1)]  

	hc.colormap = Color_Map(data_values, colors)
	color_surface(surf, hc, caps_only = False, auto_update = False)

# -----------------------------------------------------------------------------
#
def color_surface_cylinder(surf):
	writeMessageToLog("Color cylindrically")
	from SurfaceColor import color_surface, Cylinder_Color, Color_Map
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
	writeMessageToLog("%.3f,%.3f"%(cmin,cmax))
	#key: red,green,blue,opacity
	#order: orange, yellow, green, cyan, blue
	colors = [(0.750,0.375,0.067,1), (0.750,0.750,0.067,1), (0.375,0.750,0.067,1), (0.067,0.750,0.067,1), (0.067,0.750,0.750,1)]  

	cc.colormap = Color_Map(data_values, colors)
	color_surface(surf, cc, caps_only = False, auto_update = False)

# -----------------------------------------------------------------------------
#
def save_image(path, format):

	# propagate changes from C++ layer back to Python
	# can also be done via Midas module: Midas.wait(1)
	chimera.update.checkForChanges()

	# save an image
	chimera.printer.saveImage(path, format = format)

# -----------------------------------------------------------------------------
#
def hideDust(volume, size=10):
	"""
	Hide all dust particles less than 10 voxels in size
	"""
	try:
		from HideDust import dust
		writeMessageToLog("hiding dust of size %.1f"%(size))
		#writeMessageToLog(str(dir(dust))
		#writeMessageToLog(str(help(dust))
		dust.hide_dust(volume, 'size', limit, auto_update = True)
		#runChimCommand('hide dust # %d'%(size))
	except:
		writeMessageToLog("skipping hide dust")
		pass

# -----------------------------------------------------------------------------
#
def render_volume(tmp_path, vol_path, contour=1.5, 
	zoom_factor=1.0, image_size=(128, 128), imgFormat="PNG", sym="C"):

	chimera.viewer.windowSize = image_size

	file_type='mrc'
	v = openVolumeData(tmp_path, file_type, contour)

	from _surface import SurfaceModel
	from chimera import openModels as om
	surfs = om.list(modelTypes=[SurfaceModel])

	runChimCommand('scale %.3f' % zoom_factor)   # Zoom

	if sym[:4].lower() == 'icos':
		process_icosahedral(v, surfs, vol_path, imgFormat="PNG")
	elif sym.lower()[0] == 'd':
		process_dsym(v, surfs, vol_path, imgFormat="PNG")
	elif sym.lower() == 'c1':
		process_asymmetric(v, surfs, vol_path, imgFormat="PNG")
	else:
		process_csym(v, surfs, vol_path, imgFormat="PNG")

# -----------------------------------------------------------------------------
#
def process_icosahedral(v, surfs, vol_path, imgFormat="PNG"):
	hideDust(v, 2)
	for s in surfs:
		color_surface_radially(s)

	save_image(vol_path+'.001.png', format=imgFormat)

	writeMessageToLog("turn: down 3-fold axis")
	runChimCommand('turn y 37.377')
	save_image(vol_path+'.002.png', format=imgFormat)
	
	writeMessageToLog("turn: viper orientation (2 fold)")
	runChimCommand('turn y 20.906')
	save_image(vol_path+'.003.png', format=imgFormat) 

	writeMessageToLog("turn: get clipped view")
	time.sleep(0.5)
	runChimCommand('mclip #0 coords screen axis z')
	runChimCommand('wait')
	time.sleep(0.5)
	runChimCommand('ac cc')
	runChimCommand('wait')
	time.sleep(0.5)
	save_image(vol_path+'.006.png', format=imgFormat)

# -----------------------------------------------------------------------------
#
def process_asymmetric(v, surfs, vol_path, imgFormat="PNG"):
	hideDust(v, 10)
	for s in surfs:
		color_surface_height(s)
	writeMessageToLog("turn: get top view")
	runChimCommand("turn x 180")

	tilt = 15
	runChimCommand("turn x %d"%(-tilt))
	increment = 5
	nsteps = int(360/increment)
	for i in range(nsteps):
		filename = "%s.%03d.%s"%(vol_path, i, imgFormat.lower())
		save_image(filename, format=imgFormat)
		writeMessageToLog("turn: rotate by %d to %d"%(increment,increment*(i+1)))
		runChimCommand("turn x %d"%(tilt))
		runChimCommand("turn y %d"%(increment))
		runChimCommand("turn x %d"%(-tilt))
	for i in range(nsteps):
		filename = "%s.%03d.%s"%(vol_path, i+nsteps, imgFormat.lower())
		save_image(filename, format=imgFormat)
		writeMessageToLog("turn: rotate by %d to %d"%(increment,increment*(i+1)))
		runChimCommand("turn x %d"%(increment))

# -----------------------------------------------------------------------------
#
def process_dsym(v, surfs, vol_path, imgFormat="PNG"):
	hideDust(v, 2)
	for s in surfs:
		color_surface_cylinder(s)
	writeMessageToLog("turn: get intermediate side view")
	runChimCommand('turn x 90')

	tilt = 30
	runChimCommand("turn x %d"%(tilt))
	increment = 15
	nsteps = int(360/increment)
	for i in range(nsteps):
		filename = "%s.%03d.%s"%(vol_path, i, imgFormat.lower())
		save_image(filename, format=imgFormat)
		writeMessageToLog("turn: rotate by %d to %d"%(increment,increment*(i+1)))
		runChimCommand("turn x %d"%(-tilt))
		runChimCommand("turn y %d"%(increment))
		runChimCommand("turn x %d"%(tilt))

# -----------------------------------------------------------------------------
#
def process_csym(v, surfs, vol_path, imgFormat="PNG"):
	hideDust(v, 5)
	for s in surfs:
		color_surface_cylinder(s)
	writeMessageToLog("turn: get intermediate side view")
	runChimCommand('turn x 90')

	tilt = 30
	runChimCommand("turn x %d"%(tilt))
	increment = 15
	nsteps = int(360/increment)
	for i in range(nsteps):
		filename = "%s.%03d.%s"%(vol_path, i, imgFormat.lower())
		save_image(filename, format=imgFormat)
		writeMessageToLog("turn: rotate by %d to %d"%(increment,increment*(i+1)))
		runChimCommand("turn x %d"%(-tilt))
		runChimCommand("turn y %d"%(increment))
		runChimCommand("turn x %d"%(tilt))


# -----------------------------------------------------------------------------
#

def runChimCommand(cmd):
	if chimlog is not None:
		f = open(chimlog, "a")
		f.write(str(cmd)+"\n")
		f.close()
		#nogui_message(cmd.strip()+"\n")
	chimera.runCommand(cmd)

# -----------------------------------------------------------------------------
#

def writeMessageToLog(msg):
	if chimlog is None:
		return
	f = open(chimlog, "a")
	f.write(str(msg)+"\n")
	f.close()

# -----------------------------------------------------------------------------
#

if True:
	env = os.environ.get('CHIMENV')
	if env is None:
		#writeMessageToLog("no environmental data")
		sys.exit(1)
	params = env.split(',')

	## change bg color	
	from chimera.colorTable import getColorByName
	white = getColorByName('white')
	chimera.viewer.background = white
	#chimera.viewer.showSilhouette = True

	tmpfile_path = params[0] #sys.argv[2]
	volume_path = params[1] #sys.argv[3]
	rundir = os.path.dirname(volume_path)
	sym = params[2] #sys.argv[4]
	contour = float(params[3]) #sys.argv[5])
	zoom_factor = float(params[4]) #sys.argv[6])

	rundir = os.path.dirname(volume_path)
	chimlog = os.path.join(rundir, "chimera.log")

	writeMessageToLog("Environmental data: "+str(params))

	render_volume(tmpfile_path, volume_path, contour, zoom_factor=zoom_factor, sym=sym)

	chimera.ChimeraExit()
	chimera.ChimeraSystemExit()
	sys.exit(1)






