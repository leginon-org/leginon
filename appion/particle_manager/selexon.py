#! /usr/bin/env python
# Python wrapper for the selexon program
# Will by default create a "jpgs" directory and save jpg images of selections & crudfinder results

import os, re, sys
import tempfile
import string
import cPickle
import data
import dbdatakeeper
import time
import convolver
import Mrc
import numarray.nd_image
import imagefun

db=dbdatakeeper.DBDataKeeper()
selexondonename='.selexondone.py'

def printHelp():
    print "\nUsage:\nselexon.py <file> template=<name> apix=<pixel> diam=<n> bin=<n> [range=<start,stop,incr>] [thresh=<threshold> or autopik=<n>] [lp=<n>] [hp=<n>] [crud or cruddiam=<n>] [crudonly] [crudblur=<n>] [crudlow=<n>] [crudhi=<n>] [box=<n>] [continue] [dbimages=<session>,<preset>]"
    print "or\nselexon.py preptemplate template=<name> apix=<pixel> bin=<n>\n"
    print "Examples:\nselexon 05jun23a_00001en.mrc template=groEL apix=1.63 diam=250 bin=4 range=0,90,10 thresh=0.45 crud"
    print "or"
    print "selexon template=groEL apix=1.63 diam=250 bin=4 range=0,90,10 thresh=0.45 crud dbimages=05jun23a,en continue\n"
    print "preptemplate       : this will prepare all your template files for selexon"
    print "template=<name>    : name should not have the extension, or number."
    print "                     groEL1.mrc, groEL2.mrc would be simply \"template=groEL\""
    print "apix=<pixel>       : angstroms per pixel (unbinned)"
    print "diam=<n>           : approximate diameter of particle (in Angstroms, unbinned)"
    print "bin=<n>            : images will be binned by this amount (default is 4)"
    print "range=<st,end,i>   : each template will be rotated from the starting angle to the"
    print "                     stop angle at the given increment"
    print "                     User can also specify ranges for each template (i.e. range1=0,60,20)"
    print "                     NOTE: if you don't want to rotate the image, leave this parameter out"
    print "thresh=<thr>       : manual cutoff for correlation peaks (0-1), don't use if want autopik"
    print "autopik=<thr>      : automatically calculate threshold, n = average number of particles per image"
    print "lp=<n>, hp=<n>     : low-pass and high-pass filter (in Angstroms) - defaults are 30 & 600\n"
    print "                     NOTE: high-pass filtering is currently disabled"
    print "crud               : run the crud finder after the particle selection"
    print "                     (will use particle diameter by default)"
    print "cruddiam=<n>       : set the diameter to use for the crud finder"
    print "                     (don't need to use the \"crud\" option if using this)"
    print "crudblur=<n>       : amount to blur the image for edge detection (default is 3.5)"
    print "crudlo=<n>         : lower limit for edge detection (0-1, default=0.6)"
    print "crudhi=<n>         : upper threshold for edge detection (0-1, default=0.95)"
    print "crudstd=<n>        : lower limit for scaling the edge detection limits (i.e. stdev of the image) (default=1= never scale)"
    print "crudonly           : only run the crud finder to check and view the settings"
    print "box=<n>            : output will be saved as EMAN box file with given box size"
    print "continue           : if this option is turned on, selexon will skip previously processed"
    print "                     micrographs"
    print "dbimages=<sess,pr> : if this option is turned on, selexon will continuously get images from the database"
    print "                     do not use this option if you are specifying particular images"
    print "\n"

    sys.exit(1)
    
def createDefaults():
    # create default values for parameters
    params={}
    params["mrcfileroot"]=''
    params["preptmplt"]='FALSE'
    params["template"]=''
    params["apix"]=0
    params["diam"]=0
    params["bin"]=4
    params["startang"]=0
    params["endang"]=90
    params["incrang"]=100
    params["thresh"]=0
    params["autopik"]=0
    params["lp"]=30
    params["hp"]=600
    params["box"]=0
    params["crud"]='FALSE'
    params["cdiam"]=0
    params["cblur"]=3.5
    params["clo"]=0.6
    params["chi"]=0.95
    params["cstd"]=1
    params["crudonly"]='FALSE'
    params["onetemplate"]='FALSE'
    params["continue"]='FALSE'
    params["multiple_range"]='FALSE'
    params["dbimages"]='FALSE'
    params["session"]=None
    params["preset"]=None
    return params

def parseInput(args):
    # check that there are enough input parameters
    if (len(args)<2 or args[1]=='help') :
        printHelp()

    # create params dictionary & set defaults
    params=createDefaults()

    lastarg=1

    # check if user just wants make template images
    if (args[1]=='preptemplate'):
        params["preptmplt"]='TRUE'
        lastarg=2

    # save the input parameters into the "params" dictionary

    # first get all images
    mrcfileroot=[]
    for arg in args[lastarg:]:
        # gather all input files into mrcfileroot list
        if '=' in  arg:
            break
        elif (arg=='crudonly' or arg=='crud'):
            break
        else:
            mrcfile=arg
            if (os.path.exists(mrcfile)):
                mrcfileroot.append(os.path.splitext(mrcfile)[0])
            else:
                print ("file '%s' does not exist \n" % mrcfile)
                sys.exit()
        lastarg+=1
    params["mrcfileroot"]=mrcfileroot

    # next get all selection parameters
    for arg in args[lastarg:]:
        elements=arg.split('=')
        if (elements[0]=='template'):
            params["template"]=elements[1]
        elif (elements[0]=='apix'):
            params["apix"]=float(elements[1])
        elif (elements[0]=='diam'):
            params["diam"]=int(elements[1])
        elif (elements[0]=='bin'):
            params["bin"]=int(elements[1])
        elif (elements[0]=='range'):
            angs=elements[1].split(',')
            if (len(angs)==3):
                params["startang"]=float(angs[0])
                params["endang"]=float(angs[1])
                params["incrang"]=float(angs[2])
            else:
                print "range must include start & stop angle & increment"
                sys.exit(1)
        elif (re.match('range\d+',elements[0])):
            num=elements[0][-1]
            angs=elements[1].split(',')
            if (len(angs)==3):
                params["startang"+num]=float(angs[0])
                params["endang"+num]=float(angs[1])
                params["incrang"+num]=float(angs[2])
                params["multiple_range"]='TRUE'
            else:
                print "range must include start & stop angle & increment"
                sys.exit(1)
        elif (elements[0]=='thresh'):
            params["thresh"]=float(elements[1])
        elif (elements[0]=='autopik'):
            params["autopik"]=float(elements[1])
        elif (elements[0]=='lp'):
            params["lp"]=float(elements[1])
        elif (elements[0]=='hp'):
            params["hp"]=float(elements[1])
        elif (elements[0]=='box'):
            params["box"]=int(elements[1])
        elif (arg=='crud'):
            params["crud"]='TRUE'
        elif (elements[0]=='cruddiam'):
            params["crud"]='TRUE'
            params["cdiam"]=int(elements[1])
        elif (elements[0]=='crudblur'):
            params["cblur"]=float(elements[1])
        elif (elements[0]=='crudlo'):
            params["clo"]=float(elements[1])
        elif (elements[0]=='crudhi'):
            params["chi"]=float(elements[1])
        elif (elements[0]=='crudstd'):
            params["cstd"]=float(elements[1])
        elif (arg=='crudonly'):
            params["crudonly"]='TRUE'
        elif (arg=='continue'):
            params["continue"]='TRUE'
        elif (elements[0]=='dbimages'):
            dbinfo=elements[1].split(',')
            if len(dbinfo) == 2:
                params['session']=dbinfo[0]
                params['preset']=dbinfo[1]
                params["dbimages"]='TRUE'
                params["continue"]='TRUE' # continue should be on for dbimages option
            else:
                print "dbimages must include both session and preset parameters"
                sys.exit()
        else:
            print "undefined parameter '"+arg+"'\n"
            sys.exit(1)
        
    # determine win_size, borderwidth, & dwn pixel size
    if (params["apix"]>0):
        params["win_size"]=int(1.5 * params["diam"]/params["apix"]/params["bin"])
        params["borderwidth"]=params["win_size"]/2
        params["apixdwn"]=params["apix"]*params["bin"]

    # find the number of template files
    if (params["crudonly"]=='FALSE'):
        params=checkTemplates(params)
    return params

def checkTemplates(params):
    # determine number of template files
    # if using 'preptemplate' option, will count number of '.mrc' files
    # otherwise, will count the number of '.dwn.mrc' files

    if (params["preptmplt"]=='TRUE'):
        ext='.mrc'
    else:
        ext='.dwn.mrc'

    name=params["template"]
    stop=0 
    n=0    # number of template files
    
    # count number of template images.
    # if a template image exists with no number after it
    # counter will assume that there is only one template
    while (stop==0):
        if (os.path.exists(name+ext)):
            n=n+1
            params["onetemplate"]='TRUE'
            stop=1
        elif (os.path.exists(name+str(n+1)+ext)):
            n=n+1
        else:
            stop=1

    if (n==0):
        print "There are no template images found with basename \""+name+"\"\n"
        sys.exit(1)
    else :
        params["classes"]=n

    return(params)

def dwnsizeImg(params,img):
    #downsize and filter leginon image     
    imagedata=getImageData(img)    
    bin=params['bin']
    print "downsizing", img
    im=binImg(imagedata['image'],bin)

    print "filtering", img
    apix=params['apix']*bin
    im=filterImg(im,apix,params['lp'])
    Mrc.numeric_to_mrc(im,(img+'.dwn.mrc'))
    return

def dwnsizeTemplate(params,img):
    #downsize and filter arbitary MRC template image
    bin=params['bin']
    im=Mrc.mrc_to_numeric(img+'.mrc')
    print "downsizing", img
    im=binImg(im,bin)

    print "filtering",img
    apix=params['apix']*bin
    im=filterImg(im,apix,params['lp'])
    Mrc.numeric_to_mrc(im,(img+'.dwn.mrc'))
    return

def binImg(img,binning):
    #bin image using leginon imagefun library
    #img must be a numarray image
    return(imagefun.bin(img,binning))
    
def filterImg(img,apix,res):
    # low pass filter image to res resolution
    if res==0:
        print "Skipping low pass filter"
        return(img)
    else:
        c=convolver.Convolver()
        sigma=(res/apix)/3.0
        kernel=convolver.gaussian_kernel(sigma)
        #Mrc.numeric_to_mrc(kernel,'kernel.mrc')
    return(c.convolve(image=img,kernel=kernel))
           
def runFindEM(params,file):
    # run FindEM
    tmplt=params["template"]
    numcls=params["classes"]
    pixdwn=str(params["apixdwn"])
    d=str(params["diam"])
    if (params["multiple_range"]=='FALSE'):
        strt=str(params["startang"])
        end=str(params["endang"])
        incr=str(params["incrang"])
    bw=str(params["borderwidth"])

    classavg=1
    while classavg<=params["classes"]:
        # first remove the existing cccmaxmap** file
        cccfile="cccmaxmap%i00.mrc" %classavg
        if (os.path.exists(cccfile)):
            os.remove(cccfile)

        if (params["multiple_range"]=='TRUE'):
            strt=str(params["startang"+str(classavg)])
            end=str(params["endang"+str(classavg)])
            incr=str(params["incrang"+str(classavg)])
        fin=os.popen('${FINDEM_PATH}/FindEM_SB','w')
        fin.write(file+".dwn.mrc\n")
        if (params["onetemplate"]=='TRUE'):
            fin.write(tmplt+".dwn.mrc\n")
        else:
            fin.write(tmplt+str(classavg)+".dwn.mrc\n")
        fin.write("-200.0\n")
        fin.write(pixdwn+"\n")
        fin.write(d+"\n")
        fin.write(str(classavg)+"00\n")
        fin.write(strt+','+end+','+incr+"\n")
        fin.write(bw+"\n")
        fin.flush
        print "running findEM"
        classavg=classavg+1
        
def findPeaks(params,file):
    # create tcl script to process the cccmaxmap***.mrc images & find peaks
    tmpfile=tempfile.NamedTemporaryFile()
    imgsize=int(getImgSize(file))
    wsize=str(params["win_size"])
    clsnum=str(params["classes"])
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
        i=i+1
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
    f=os.popen('viewit '+tmpfile.name)
    result=f.readlines()
    line=result[-2].split()
    peaks=line[0]
    print "found",peaks,"peaks"

def createJPG(params,img):
    # create a jpg image to visualize the final list of targetted particles
    tmpfile=tempfile.NamedTemporaryFile()

    # create "jpgs" directory if doesn't exist
    if not (os.path.exists("jpgs")):
        os.mkdir("jpgs")
    
    scale=str(params["bin"])
    file=img
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
    f=os.popen('viewit '+tmpfile.name)
    result=f.readlines()
    
def findCrud(params,file):
    # run the crud finder
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
    image=Mrc.mrc_to_numeric(file+".mrc")
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
    if (params["crudonly"]=='FALSE'):
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
    if (params["crudonly"]=='FALSE'):
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
    if (params["crudonly"]=='FALSE'):
        cmdlist.append("  -zhsuper_prtl 0 $xcenter $ycenter "+size+" $thickness $pixel_value\n")
    cmdlist.append("  -store outlined_img ss1\n")
    if (params["crudonly"]=='FALSE'):
        cmdlist.append("}\n")
        cmdlist.append("close $fp\n")
    cmdlist.append("-load ss1 outlined_img\n")
    cmdlist.append("-oformat JPEG -o \"jpgs/"+file+".a.pik.nocrud.jpg\"\n")
    if (params["crudonly"]=='FALSE'):
        cmdlist.append("puts \"$x particles rejected due to being inside a crud.\"\n")
    cmdlist.append("exit\n")

    tclfile=open(tmpfile.name,'w')
    tclfile.writelines(cmdlist)
    tclfile.close()
    f=os.popen('viewit '+tmpfile.name)
    result=f.readlines()
    line=result[-2].split()
    reject=line[1]
    print "crudfinder rejected",reject,"particles"
    
def prepTemplate(params):
    # check that parameters are set:
    if (params["apix"]==0 or params["template"]=='' or params["bin"]==0):
        printHelp()

    # go through the template mrc files and downsize & filter them
    i=1
    num=params["classes"]
    name=params["template"]
    while i<=num:
        if params["onetemplate"]=='TRUE':
            mrcfile=name
        else:
            mrcfile=name+str(i)
        os.system("fix_mrc "+mrcfile+".mrc")
        dwnsizeTemplate(params,mrcfile)
        i=i+1
    print "\ndownsize & filtered "+str(num)+" file(s) with root \""+params["template"]+"\"\n"
    sys.exit(1)
    
def pik2Box(params,file):
    box=params["box"]
    if (params["crud"]=='TRUE'):
        fname="pikfiles/"+file+".a.pik.nocrud"
    else:
        fname="pikfiles/"+file+".a.pik"
        
    pfile=open(fname,"r")
    bfile=open(file+".box","w")
    piklist=[]
    for line in pfile:
        elements=line.split(' ')
        xcenter=int(elements[1])
        ycenter=int(elements[2])
        xcoord=xcenter - (box/2)
        ycoord=ycenter - (box/2)
        if (xcoord>0 and ycoord>0):
            piklist.append(str(xcoord)+"\t"+str(ycoord)+"\t"+str(box)+"\t"+str(box)+"\t-3\n")
    pfile.close()
    bfile.writelines(piklist)
    bfile.close()

    print "results written to",file+".box\n"

def getImgSize(fname):
    # get image size (in pixels) of the given mrc file
    imageq=data.AcquisitionImageData(filename=fname)
    imagedata=db.query(imageq, results=1, readimages=False)
    if imagedata:
        size=int(imagedata[0]['camera']['dimension']['y'])
        return(size)
    else:
        print "Image", fname," not found in db"
        sys.exit()
    return(size)

def writeSelexLog(commandline):
    f=open('.selexonlog','a')
    out=""
    for n in commandline:
        out=out+n+" "
    f.write(out)
    f.write("\n")
    f.close()

def getDoneDict():
    if os.path.exists(selexondonename):
        # unpickle previously modified dictionary
        f=open(selexondonename,'r')
        donedict=cPickle.load(f)
        f.close()
    else:
        #set up dictionary
        donedict={}
    return (donedict)

def writeDoneDict(donedict):
    f=open(selexondonename,'w')
    cPickle.dump(donedict,f)
    f.close()

def doneCheck(donedict,im):
    # check to see if image has been processed yet and
    # append dictionary if it hasn't
    # this may not be the best way to do this
    if donedict.has_key(im):
        pass
    else:
        donedict[im]=None
    return

def getImageData(imagename):
    # get image data object from database
    imagedataq = data.AcquisitionImageData(filename=imagename)
    imagedata = db.query(imagedataq, results=1)
    if imagedata:
        return imagedata[0]
    else:
        print "Image", imagename,"not found in database"
        sys.exit()

def getPixelSize(imagedata):
    # use image data object to get pixel size
    # multiplies by binning and also by 1e10 to return image pixel size in angstroms
    pixelsizeq=data.PixelSizeCalibrationData()
    pixelsizeq['magnification']=imagedata['scope']['magnification']
    pixelsizeq['tem']=imagedata['scope']['tem']
    pixelsizeq['ccdcamera'] = imagedata['camera']['ccdcamera']
    pixelsizedata=db.query(pixelsizeq, results=1)
	
    binning=imagedata['camera']['binning']['x']
    pixelsize=pixelsizedata[0]['pixelsize'] * binning
	
    return(pixelsize*1e10)

def getImagesFromDB(session,preset):
    # returns list of image names from DB
    print "Querying database for images"
    sessionq = data.SessionData(name=session)
    presetq=data.PresetData(name=preset)
    imageq=data.AcquisitionImageData()
    imageq['preset'] = presetq
    imageq['session'] = sessionq
    # readimages=False to keep db from returning actual image
    # readimages=True could be used for doing processing w/i this script
    imagelist=db.query(imageq, readimages=False)
    images=[]
    #create list of images and make a link to them if they are not already in curr dir
    for n in imagelist:
        imagename=n['filename']
        images.append(imagename)
        imgpath=n['session']['image path'] + '/' + imagename + '.mrc'
        if not os.path.exists((imagename + '.mrc')):
            command=('ln -s %s .' %  imgpath)
            print command
            os.system(command)
    return (images)
    
#-----------------------------------------------------------------------

if __name__ == '__main__':
    # record command line
    writeSelexLog(sys.argv)
    # parse command line input
    params=parseInput(sys.argv)
    # unpickle dictionary of previously processed images
    donedict=getDoneDict()

    # check to see if user only wants to downsize & filter template files
    if (params["preptmplt"]=='TRUE'):
        prepTemplate(params)

    # get list of input images, since wildcards are supported
    if params['dbimages']=='TRUE':
        images=getImagesFromDB(params['session'],params['preset'])
    else:
        images=params["mrcfileroot"]

    # check to see if user only wants to run the crud finder
    if (params["crudonly"]=='TRUE'):
        if (params["crud"]=='TRUE' and params["cdiam"]==0):
            print "\nError: both \"crud\" and \"crudonly\" are set, choose one or the other.\n"
            sys.exit(1)
        if (params["diam"]==0): # diameter must be set
            print "\nError: please input the diameter of your particle\n\n"
            sys.exit(1)
    	# create directory to contain the 'crud' files
    	if not (os.path.exists("crudfiles")):
        	os.mkdir("crudfiles")
        for img in images:
            findCrud(params,img)
        sys.exit(1)
        
    # check for wrong or missing inputs
    if (params["thresh"]==0 and params["autopik"]==0):
        print "\nError: neither manual threshold or autopik parameters are set, please set one.\n"
        sys.exit(1)
    if (params["apix"]==0):
        print "\nError: no pixel size has been entered\n\n"
        sys.exit(1)
    if (params["diam"]==0):
        print "\nError: please input the diameter of your particle\n\n"
        sys.exit(1)
    if len(params["mrcfileroot"]) > 0 and params["dbimages"]=='TRUE':
        print len(images)
        print "\nError: dbimages can not be specified if particular images have been specified"
        sys.exit(1)

    # create directory to contain the 'pik' files
    if not (os.path.exists("pikfiles")):
        os.mkdir("pikfiles")

    # run selexon
    notdone=True
    while notdone:
        for img in images:
            # if continue option is true, check to see if image has already been processed
            doneCheck(donedict,img)
            if (params["continue"]=='TRUE'):
                if donedict[img]:
                    print img,'already processed. To process again, remove "continue" option.'
                    continue

            # run FindEM
            dwnsizeImg(params,img)
            runFindEM(params,img)
            findPeaks(params,img)

            # if no particles were found, skip rest and go to next image
            if not (os.path.exists("pikfiles/"+img+".a.pik")):
                print "no particles found in \""+img+".mrc\"\n"
                # write results to dictionary
                donedict[img]=True
                writeDoneDict(donedict)
                continue

            # run the crud finder on selected particles if specified
            if (params["crud"]=='TRUE'):
                if not (os.path.exists("crudfiles")):
        	    os.mkdir("crudfiles")
                findCrud(params,img)
                # if crudfinder removes all the particles, go to next image
                if not (os.path.exists("pikfiles/"+img+".a.pik.nocrud")):
                    print "no particles left after crudfinder in \""+img+".mrc\"\n"
                    # write results to dictionary
                    donedict[img]=True
                    writeDoneDict(donedict)
                    continue

            # create jpg of selected particles if not created by crudfinder
            if (params["crud"]=='FALSE'):
                createJPG(params,img)

            # convert resulting pik file to eman box file
            if (params["box"]>0):
                pik2Box(params,img)

            # write results to dictionary
            donedict[img]=True
            writeDoneDict(donedict)
	    

        if params["dbimages"]=='TRUE':
            notdone=True
            print "Waiting one minute for new images"
            time.sleep(60)
            images=getImagesFromDB(params['session'],params['preset'])
        else:
            notdone=False

