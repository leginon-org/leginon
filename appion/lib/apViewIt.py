#Old ViewIt functions

#pythonlib
import os
import tempfile
#pyami
from pyami import mrc
from pyami import imagefun
#appion
import apDatabase

def createImageLinks(imagelist):
	"""
	make a link to all images in list if they are not already in curr dir
	"""
	for n in imagelist:
		imagename=n['filename']
		imgpath=n['session']['image path'] + '/' + imagename + '.mrc'
		if not os.path.exists((imagename + '.mrc')):
			command=('ln -s %s .' %  imgpath)
			print command
			subprocess.Popen(command, shell=True)
	return

def createJPG(params,img):
	"""
	create a jpg image to visualize the final list of targetted particles
	"""
	tmpfile = tempfile.NamedTemporaryFile()

	# create "jpgs" directory if doesn't exist
	if not (os.path.exists("jpgs")):
		os.mkdir("jpgs")

	scale=str(params["bin"])
	file=img['filename']
	size=str(int(params["diam"]/30)) #size of cross to draw

	cmdlist=[]
	cmdlist.append("#!/usr/bin/env viewit\n")
	cmdlist.append("source $env(SELEXON_PATH)/graphics.tcl\n")
	cmdlist.append("source $env(SELEXON_PATH)/io_subs.tcl\n")
	cmdlist.append("set pick [read_list pikfiles/"+file+".a.pik]\n")
	cmdlist.append("set num_picks [llength $pick]\n")
	cmdlist.append("for {set x 0} {$x < $num_picks} {incr x} {\n")
	cmdlist.append("  set apick [lindex $pick $x]\n")
	cmdlist.append("  set filename [lindex $apick 0]\n")
	cmdlist.append("  set xcord    [expr round ([lindex $apick 1]/"+scale+")]\n")
	cmdlist.append("  set ycord    [expr round ([lindex $apick 2]/"+scale+")]\n")
	cmdlist.append("  lappend particles($filename) [list $filename $xcord $ycord]\n}\n")
	cmdlist.append("set thickness 2\n")
	cmdlist.append("set pixel_value 255\n")
	cmdlist.append("set searchid [array startsearch particles ]\n")
	cmdlist.append("set filename [array nextelement particles $searchid]\n")
	cmdlist.append('while { $filename != ""} {\n');
	cmdlist.append("  set particles_list $particles($filename)\n")
	cmdlist.append("  if { [llength pikfiles/"+file+".a.pik] > 0 } {\n")
	cmdlist.append("    -iformat MRC -i [file join . $filename] -collapse\n")
	cmdlist.append("    set x "+scale+"\n")
	cmdlist.append("    while { $x > 1} {\n-scale 0.5 0.5\nset x [expr $x / 2]\n}\n")
	cmdlist.append("    -linscl 0 255\n")
	cmdlist.append("    draw_points $particles_list 0 "+size+" $thickness $pixel_value\n")
	cmdlist.append("    -oformat JPEG -o \"jpgs/$filename.prtl.jpg\"\n}\n")
	cmdlist.append("  set filename [array nextelement particles $searchid]\n}\n")
	cmdlist.append("array donesearch particles $searchid\nexit\n")

	tclfile=open(tmpfile.name,'w')
	tclfile.writelines(cmdlist)
	tclfile.close()
	f=subprocess.Popen('viewit '+tmpfile.name, shell=True)
	result=f.readlines()
	f.close()


def findCrud(params,img):
	"""
	run the viewit crud finder
	"""
	file = img['filename']
	tmpfile=tempfile.NamedTemporaryFile()

	# create "jpgs" directory if doesn't exist
	if not (os.path.exists("jpgs")):
		os.mkdir("jpgs")

	# remove crud pik file if it exists
	if (os.path.exists("pikfiles/"+file+".a.pik.nocrud")):
		os.remove("pikfiles/"+file+".a.pik.nocrud")

	# remove crud info file if it exists
	if (os.path.exists("crudfiles/"+file+".crud")):
		os.remove("crudfiles/"+file+".crud")

	diam=str(params["diam"]/4)
	cdiam=str(params["cdiam"]/4)
	if (params["cdiam"]==0):
		cdiam=diam
	scale=str(params["bin"])
	size=str(int(params["diam"]/30)) #size of cross to draw    
	sigma=str(params["cblur"]) # blur amount for edge detection
	low_tn=float(params["clo"]) # low threshold for edge detection
	high_tn=float(params["chi"]) # upper threshold for edge detection
	standard=float(params["cstd"]) # lower threshold for full scale edge detection
	pm="2.0"
	am="3.0" 

	# scale the edge detection limit if the image standard deviation is lower than the standard
	# This creates an edge detection less sensitive to noises in mostly empty images
	image=mrc.read(file+".mrc")
	imean=imagefun.mean(image)
	istdev=imagefun.stdev(image,known_mean=imean)
	print imean,istdev
	low_tns=low_tn/(istdev/standard)
	high_tns=high_tn/(istdev/standard)
	if (low_tns > 1.0):
		low_tns=1.0
	if (low_tns < low_tn):
		low_tns=low_tn
	if (high_tns > 1.0):
		high_tns=1.0
	if (high_tns < high_tn):
		high_tns=high_tn
	high_t=str(high_tns)
	low_t=str(low_tns)
	print high_tns,low_tns



	cmdlist=[]
	cmdlist.append("#!/usr/bin/env viewit\n")
	cmdlist.append("source $env(SELEXON_PATH)/io_subs.tcl\n")
	cmdlist.append("source $env(SELEXON_PATH)/image_subs.tcl\n")
	if (params["crudonly"]==False):
		cmdlist.append("set x 0\n")
		cmdlist.append("set currentfile \"not_a_valid_file\"\n")
		cmdlist.append("set fp [open pikfiles/"+file+".a.pik r]\n")
		cmdlist.append("while {[gets $fp apick ] >= 0} {\n")
		cmdlist.append("  set xcenter    [expr [lindex $apick 1] / "+scale+"]\n")
		cmdlist.append("  set ycenter    [expr [lindex $apick 2] / "+scale+"]\n")
		cmdlist.append("  if { [string compare $currentfile "+file+".mrc] != 0 } {\n")
		cmdlist.append("    if { [string compare $currentfile \"not_a_valid_file\"] != 0 } {\n")
		cmdlist.append("      -load ss1 outlined_img\n")
		cmdlist.append("      -oformat JPEG -o \"jpgs/"+file+".a.pik.nocrud.jpg\"}\n")
	cmdlist.append("    -iformat MRC -i [file join . "+file+".mrc] -collapse\n")
	cmdlist.append("    set x "+scale+"\n")
	if (params["bin"]>1):
		cmdlist.append("    -store orig_img ss1\n")
		cmdlist.append("    while { $x > 1} {\n")
		cmdlist.append("      -scale 0.5 0.5\n")
		cmdlist.append("      set x [expr $x / 2]\n")
		cmdlist.append("    }\n")    
	cmdlist.append("    -store scaled_img ss1\n")
	cmdlist.append("    set imgheight [get_rows]\n")
	cmdlist.append("    set imgwidth  [get_cols]\n")
	cmdlist.append("    puts \"image size is now scaled to $imgheight X $imgwidth\"\n")
	cmdlist.append("    set list_t [expr round ("+pm+" * 3.1415926 * "+cdiam+" / "+scale+")]\n")
	cmdlist.append("    set radius [expr "+cdiam+" / 2.0 / "+scale+"]\n")
	cmdlist.append("    set area_t  [expr round("+am+" * 3.1415926 * $radius * $radius)]\n")
	cmdlist.append("    puts \"binned radius is $radius, binned list_t = $list_t, binned area_t = $area_t\"\n")
	cmdlist.append("    set iter 3\n")
	cmdlist.append("    -zhcanny_edge "+sigma+" "+low_t+" "+high_t+" tmp.mrc\n")
	cmdlist.append("    -zhimg_dila $iter\n")
	cmdlist.append("    -zhimg_eros $iter\n")
	cmdlist.append("    -zhimg_label\n")
	cmdlist.append("    -zhprun_lpl LENGTH $list_t\n")
	cmdlist.append("    -zhmerge_plgn INSIDE\n")
	cmdlist.append("    -zhptls_chull\n")
	cmdlist.append("    -zhprun_plgn BYSIZE $area_t\n")
	cmdlist.append("    -zhmerge_plgn CONVEXHULL\n")
	cmdlist.append("    set zmet [-zhlpl_attr]\n")
	cmdlist.append("    set currentfile "+file+".mrc\n")
	cmdlist.append("    set fic [open crudfiles/"+file+".crud w+]\n")
	cmdlist.append("    puts $fic $zmet\n")
	cmdlist.append("    close $fic\n")
	cmdlist.append("    -store convex_hulls ss1\n")
	cmdlist.append("    set line_width 2\n")
	cmdlist.append("    set line_intensity 0\n")
	cmdlist.append("    -xchg\n")
	cmdlist.append("    -load ss1 scaled_img\n")
	cmdlist.append("    -linscl 0 255\n")
	cmdlist.append("    -xchg\n")
	cmdlist.append("    -zhsuper_plgn $line_width $line_intensity 1\n")
	cmdlist.append("    -xchg\n")
	cmdlist.append("    -store outlined_img ss1\n")
	cmdlist.append("    -load ss1 convex_hulls\n")
	if (params["crudonly"]==False):
		cmdlist.append("    set currentfile "+file+".mrc\n")
		cmdlist.append("  } else {\n")
		cmdlist.append("    -load ss1 convex_hulls}\n")
		cmdlist.append("  set st [-zhinsd_plgn $xcenter $ycenter]\n")
		cmdlist.append("  if {[string equal $st \"o\" ]} {\n")
		cmdlist.append("    set fid [open pikfiles/"+file+".a.pik.nocrud a+]\n")
		cmdlist.append("    puts $fid $apick\n")
		cmdlist.append("    close $fid\n")
		cmdlist.append("  } else {\n")
		cmdlist.append("    puts \"reject $apick because st = $st\"\n")
		cmdlist.append("    incr x}\n")
	cmdlist.append("  set thickness 2\n")
	cmdlist.append("  set pixel_value 255\n")
	cmdlist.append("  -load ss1 outlined_img\n")
	if (params["crudonly"]==False):
		cmdlist.append("  -zhsuper_prtl 0 $xcenter $ycenter "+size+" $thickness $pixel_value\n")
	cmdlist.append("  -store outlined_img ss1\n")
	if (params["crudonly"]==False):
		cmdlist.append("}\n")
		cmdlist.append("close $fp\n")
	cmdlist.append("-load ss1 outlined_img\n")
	cmdlist.append("-oformat JPEG -o \"jpgs/"+file+".a.pik.nocrud.jpg\"\n")
	if (params["crudonly"]==False):
		cmdlist.append("puts \"$x particles rejected due to being inside a crud.\"\n")
	cmdlist.append("exit\n")

	tclfile=open(tmpfile.name,'w')
	tclfile.writelines(cmdlist)
	tclfile.close()
	f=subprocess.Popen('viewit '+tmpfile.name, shell=True)
	result=f.readlines()
	line=result[-2].split()
	reject=line[1]
	print "crudfinder rejected",reject,"particles"
	f.close()
	return

def findPeaks(params,img):
	"""
	create tcl script to process the cccmaxmap***.mrc images & find peaks
	"""
	file = img['filename']
	tmpfile=tempfile.NamedTemporaryFile()
	imgsize=int(apDatabase.getImgSize(img))
	wsize=str(int(1.5 * params["diam"]/params["apix"]/params["bin"]))
	clsnum=str(len(params['templatelist']))
	cutoff=str(params["thresh"])
	scale=str(params["bin"])
	sz=str(imgsize/params["bin"])
	min_thresh="0.2"

	# remove existing *.pik files
	i=1
	while i<=int(clsnum):
		fname="pikfiles/%s.%i.pik" % (file,i)
		if (os.path.exists(fname)):
			os.remove(fname)
			print "removed existing file:",fname
		i+=1
	if (os.path.exists("pikfiles/"+file+".a.pik")):
		os.remove("pikfiles/"+file+".a.pik")

	cmdlist=[]
	cmdlist.append("#!/usr/bin/env viewit\n")
	cmdlist.append("source $env(SELEXON_PATH)/graphics.tcl\n")
	cmdlist.append("source $env(SELEXON_PATH)/io_subs.tcl\n")
	cmdlist.append("-iformat MRC\nif { "+clsnum+" > 1} {\n")
	cmdlist.append("  for {set x 1 } { $x <= "+clsnum+" } {incr x } {\n")
	cmdlist.append("    -i cccmaxmap${x}00.mrc -collapse\n")
	# run auto threshold if no threshold is set
	if (params["thresh"]==0):
		autop=str(params["autopik"])
		# set number of bins for histogram
		nbins=str(int(params["autopik"]/20))
		cmdlist.append("    set peaks [-zhimg_peak BYNUMBER "+autop+" "+wsize+" ]\n")
		cmdlist.append("    set peak_hist [-zhptls_hist "+nbins+"]\n")
		cmdlist.append("    set threshold [-zhhist_thresh  BYZHU 0.02]\n")
		cmdlist.append("    if { $threshold < "+min_thresh+" } {\n")
		cmdlist.append("      set threshold "+min_thresh+"}\n")
		cmdlist.append("    set final_peaks [list]\n")
		cmdlist.append("    for {set y 0} {$y < [llength $peaks] } {incr y } {\n")
		cmdlist.append("      set apick [lindex $peaks $y]\n")
		cmdlist.append("      if { [lindex $apick 3] > $threshold } {")
		cmdlist.append("        lappend final_peaks $apick} }\n")
		cmdlist.append("    write_picks "+file+".mrc $final_peaks "+scale+" pikfiles/"+file+".$x.pik\n}\n}\n")
	else:
		cmdlist.append("    set peaks [-zhimg_peak BYVALUE "+cutoff+" "+wsize+" ]\n")
		cmdlist.append("    write_picks "+file+".mrc $peaks "+scale+" pikfiles/"+file+".$x.pik\n}\n}\n")

	cmdlist.append("-dim 2 "+sz+" "+sz+" -unif -1.0\n")
	cmdlist.append("-store cccmaxmap_max\n")
	cmdlist.append("for {set x 1 } { $x <= "+clsnum+" } {incr x } {\n")
	cmdlist.append("  -i cccmaxmap${x}00.mrc -collapse\n")
	cmdlist.append("  -store cccmaxmap\n")
	cmdlist.append("  -load ss1 cccmaxmap_max\n")
	cmdlist.append("  -load ss2 cccmaxmap\n")
	cmdlist.append("  -zhreg_max\n")
	cmdlist.append("  -store cccmaxmap_max ss1\n}\n")
	cmdlist.append("-load ss1 cccmaxmap_max\n")
	if (params["thresh"]==0):
		cmdlist.append("set peaks [-zhimg_peak BYNUMBER "+autop+" "+wsize+"]\n")
		cmdlist.append("set peak_hist [-zhptls_hist "+nbins+"]\n")
		cmdlist.append("set threshold [-zhhist_thresh  BYZHU 0.02]\n")
		cmdlist.append("if { $threshold < "+min_thresh+"} {\n")
		cmdlist.append("  set threshold "+min_thresh+"}\n")
		cmdlist.append("for {set x 0} {$x < [llength $peaks] } {incr x } {\n")
		cmdlist.append("  set apick [lindex $peaks $x]\n")
		cmdlist.append("  if { [lindex $apick 3] > $threshold } {")
		cmdlist.append("    lappend final_peaks $apick} }\n")
		cmdlist.append("write_picks "+file+".mrc $final_peaks "+scale+" pikfiles/"+file+".a.pik\n")
	else:
		cmdlist.append("set peaks [-zhimg_peak BYVALUE "+cutoff+" "+wsize+"]\n")
		cmdlist.append("puts \"$peaks\"\n")
		cmdlist.append("write_picks "+file+".mrc $peaks "+scale+" pikfiles/"+file+".a.pik\nexit\n")

	tclfile=open(tmpfile.name,'w')
	tclfile.writelines(cmdlist)
	tclfile.close()
	f=subprocess.Popen('viewit '+tmpfile.name, shell=True)
	result=f.readlines()
	if (params["thresh"]!=0):
		line=result[-2].split()
		peaks=line[0]
		print peaks,"peaks were extracted"
	f.close()
