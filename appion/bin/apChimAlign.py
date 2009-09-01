# -----------------------------------------------------------------------------
# Example script for fitting one map in another without the graphical user
# interface.
#
#			 chimera --nogui apChimAlign.py
#
#

# python
import os
import sys
import glob
import random
# chimera
from chimera import runCommand
from VolumeViewer import open_volume_file
from VolumeViewer.volume import default_settings
from FitMap import map_points_and_weights, motion_to_maximum
import Matrix

default_settings.set('limit_voxel_count', False)

def fit_map_in_map(map1, map2,
		initial_map1_transform = None,
		map1_threshold = None,
		ijk_step_size_min = 0.01,		# Grid index units
		ijk_step_size_max = 1.5,		 # Grid index units
		max_steps = 10000,
		optimize_translation = True,
		optimize_rotation = True):

	# Files have to have file suffix indicating volume format.
	if initial_map1_transform:
		xf = Matrix.chimera_xform(initial_map1_transform)
		map1.surface_model().openState.globalXform(xf)
		
	use_threshold = (map1_threshold != None)
	points, point_weights = map_points_and_weights(map1, use_threshold)

	if len(points) == 0:
		if use_threshold:
			print 'No grid points above map threshold.'
		else:
			print 'Map has no non-zero values.'
		return

	move_tf, stats = motion_to_maximum(points, point_weights, map2, max_steps,
		ijk_step_size_min, ijk_step_size_max,
		optimize_translation, optimize_rotation)

	if initial_map1_transform:
		move_tf = Matrix.multiply_matrices(move_tf, initial_map1_transform)

	header = ('\nFit map %s in map %s using %d points\n'
		% (map1.name, map2.name, stats['points']) +
		'	correlation = %.4g, overlap = %.4g\n'
		% (stats['correlation'], stats['overlap']) +
		'	steps = %d, shift = %.3g, angle = %.3g degrees\n'
		% (stats['steps'], stats['shift'], stats['angle']))
	print header

	#tfs = Matrix.transformation_description(move_tf)
	#print tfs

	xf = Matrix.chimera_xform(move_tf)
	map1.surface_model().openState.globalXform(xf)



# -----------------------------------------------------------------------------
### set files
maindir = '/ami/data16/appion/09mar04b/models/emanmodel28'
maindir = '/home/vossman/Documents/papers/initmodel/initmodels-figure'
map1_path = os.path.join(maindir, 'reconemdb.mrc')

map1 = open_volume_file(map1_path)[0]
map1.set_parameters(surface_levels = [1.0])
mrcfiles = glob.glob(os.path.join(maindir, '*.mrc'))
aligndir = os.path.join(maindir, 'align/')
if not os.path.isdir(aligndir):
	os.mkdir(aligndir)
prefix = os.path.join(aligndir, 'align')
N = len(mrcfiles)
random.shuffle(mrcfiles)
for i,mrcfile in enumerate(mrcfiles):
	if os.path.basename(mrcfile)[:5] == "align":
		continue
	new_path = (prefix+os.path.basename(mrcfile))
	if os.path.isfile(new_path):
		print "----------"
		continue
	print ("\n==============================\n", 
		os.path.basename(mrcfile), 
		"\n==============================\n")
	map2 = open_volume_file(mrcfile)[0]
	map2.set_parameters(surface_levels = [1.0])
	new_path = (prefix+os.path.basename(mrcfile))
	fit_map_in_map(map1, map2, map1_threshold=1.0)
	runCommand('vop #1 resample onGrid #0 modelId %d'%(i+N))
	runCommand('volume #%d save %s'%(i+N, new_path))
	map2.close()
	runCommand('close #1')
	runCommand('close #%d'%(i+N))


if __name__ == "__main__":
	sys.stderr.write("usage: chimera --nogui apChimAlign.py")
	sys.exit(1)


