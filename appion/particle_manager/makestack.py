#! /usr/bin/env python
# Will create a stack file based on a set of input parameters using EMAN's batchboxer

import os, re, sys
import string
import data
import processingData
import dbdatakeeper

acedb=dbdatakeeper.DBDataKeeper(db='processing')
db=dbdatakeeper.DBDataKeeper()

def printHelp():
    print "\nUsage:\nmakestack.py <boxfile> [single=<stackfile>] [outdir=<path>] [ace=<n>] [boxsize=<n>] [inspected=<file>] [phaseflip] [noinvert] [spider]\n"
    print "Examples:\nmakestack.py extract/001ma.box single=stacks/start.hed ace=0.8 boxsize=180 inspected"
    print "makestack.py extract/*.box outdir=stacks/noctf/ ace=0.8 boxsize=180\n"
    print "* Supports wildcards - By default a stack file of the same name as the box file"
    print "  will be created in the current directory *\n"
    print "<boxfile>            : EMAN box file(s) containing picked particle coordinates"
    print "outdir=<path>        : Directory in which to create the stack"
    print "single=<file>        : Create a single stack containing all the boxed particles"
    print "                       (density will be inverted)"
    print "ace=<n>              : Only use micrographs with this ACE confidence value and higher"
    print "boxsize=<n>          : Make stacks with this box size"
    print "inspected=<file>     : Text file containing results of manually checked images"
    print "phaseflip            : Stack will be phase flipped using best ACE value in database"
    print "noinvert             : If writing to a single stack, images will NOT be inverted"
    print "                       (stack images are inverted by default)"
    print "spider               : Single output stack will be in SPIDER format"
    print "\n"

    sys.exit(1)
    
def createDefaults():
    # create default values for parameters
    params={}
    params["imgs"]=''
    params["outdir"]=''
    params["single"]=''
    params["ace"]=0
    params["boxsize"]=0
    params["inspected"]=''
    params["phaseflip"]='FALSE'
    params["hasace"]='FALSE'
    params["apix"]=0
    params["kv"]=0
    params["noinvert"]='FALSE'
    params["spider"]='FALSE'
    return params

def parseInput(args):
    # check that there are enough input parameters
    if (len(args)<2 or args[1]=='help') :
        printHelp()

    # create params dictionary & set defaults
    params=createDefaults()

    lastarg=1

    # first get all images
    mrcfileroot=[]
    for arg in args[lastarg:]:
        # gather all input files into mrcfileroot list
        if '=' in  arg:
            break
        elif (arg=='phaseflip'):
            break
        else:
            boxfile=arg
            if (os.path.exists(boxfile)):
                mrcfileroot.append(os.path.splitext(boxfile)[0])
            else:
                print ("file '%s' does not exist \n" % boxfile)
                sys.exit()
        lastarg+=1
    params["imgs"]=mrcfileroot

    # next get all selection parameters
    for arg in args[lastarg:]:
        elements=arg.split('=')
        if (elements[0]=='outdir'):
            params["outdir"]=elements[1]
            # make sure the directory path has '/' at end
            if not(params["outdir"][-1]=='/'):
                params["outdir"]=params["outdir"]+'/'
        elif (elements[0]=='single'):
            params["single"]=elements[1]
        elif (elements[0]=='ace'):
            params["ace"]=float(elements[1])
        elif (elements[0]=='boxsize'):
            params["boxsize"]=int(elements[1])
        elif (elements[0]=='inspected'):
            params["inspected"]=elements[1]
        elif (arg=='phaseflip'):
            params["phaseflip"]='TRUE'
        elif (arg=='noinvert'):
            params["noinvert"]='TRUE'
        elif (arg=='spider'):
            params["spider"]='TRUE'
        else:
            print "undefined parameter '"+arg+"'\n"
            sys.exit(1)
    return params
    
def getFilePath(img):
    session=img.split('_')[0] # get session from beginning of file name
    f=os.popen('dbemgetpath %s' % session)
    result=f.readlines()
    f.close()
    if (result==[]):
        print "rawdata directory does not exist!\n"
        sys.exit(1)
    else:
        words=result[0].split('\t')
        path=string.rstrip(words[1])
    return path

def checkInspected(img):
    f=open(params["inspected"],'r')
    results=f.readlines()
    status=''
    for line in results:
        words=line.split('\t')
        if (string.find(words[0],img)==0):
            status=words[1]
            status.rstrip('\n')
            break
    if (status.rstrip('\n')=='keep'):
        return 'TRUE'
    return 'FALSE'

"""       
def getAceValues(params,img):
    if (params["hasace"]=='TRUE'):
        return
    else:
        filename=img+'.mrc'
        f=os.popen('getace %s' %filename)
        lines=f.readlines()
        if (lines==''):
            print "empty!"
        f.close()
        for n in lines:
            words=n.split()
            if ('defocus1:' in words):
                df=float(words[-1])*-1e6
                params["df"]=df
            if ('confidence_d:' in words):
                conf_d=float(words[-1])
                params["conf_d"]=conf_d
            if 'confidence:' in words:
                conf=float(words[-1])
                params["conf"]=conf
            if 'pixelsize:' in words:
                apix=float(words[-1])*1e10
                params["apix"]=apix
            if 'tension:' in words:
                kv=int(words[-1])/1000
                params["kv"]=kv
        if (params["apix"]>0 and params["kv"]>0 and (params["conf"] !=0 or params["conf_d"] !=0)):
            params["hasace"]='TRUE'
        return
"""
def getAceValues(params,img):
    if params['hasace']=='TRUE':
        return
    else:
        filename=img+'.mrc'
        ctfq=processingData.ctf()
        imq=processingData.image(imagename=filename)
        ctfq['image']=imq
        ctfparams=acedb.query(ctfq)
        imagedata=db.directquery(dataclass=data.AcquisitionImageData, id=ctfparams[0]['imageId']['dbemdata|AcquisitionImageData|image'], readimages=False)
        if ctfparams[0]['imageId']['imagename'] != imagedata['filename']+'.mrc':
            print "There are serious problems with the database queries.", ctfparams[0]['imageId']['imagename'] ,'not equal to' , imagedata['filename']+'.mrc'
	    sys.exit()
	if imagedata and ctfparams:
	    if ['stig']==0:
		params['hasace']='TRUE'
		params['df']=ctfparams['defocus1']
		params['conf_d']=ctfparams['confidence_d']
		params['conf']=ctfparams['confidence']
		params['apix']=getPixelSize(imagedata)
		params['kv']=imagedata['scope']['high tension']
	    else:
		print "Skipping image", filename, "because makestack cannot handle ACE estimates with astigmatism turned on"
		params['hasace']='FALSE'
        return
            
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

        
def checkAce(img):
    conf_d=params["conf_d"]
    conf=params["conf"]
    thresh=params["ace"]
    # if either conf_d or confidence are above threshold, use this image
    if (conf_d>=thresh or conf>=thresh):
        return 'TRUE'
    return 'FALSE'

def batchBox(params, img):
    input=params["filepath"]+'/'+img+'.mrc'
    output=params["outdir"]+img+'.hed'
    dbbox=img+'.box'

    # create output directory if it does not exist
    if (params["outdir"]!='' and not os.path.exists(params["outdir"])):
        os.mkdir(params["outdir"])
           
    # write batchboxer command
    if (params["boxsize"]!=0):
        cmd="batchboxer input=%s dbbox=%s output=%s newsize=%i insideonly" %(input, dbbox, output, params["boxsize"])
    else: 
        cmd="batchboxer input=%s dbbox=%s output=%s insideonly" %(input, dbbox, output)

    print "boxing",input
    f=os.popen(cmd)
    f.close()
    
def phaseFlip(params,img):
    input=params["outdir"]+img+'.hed'
    output=params["outdir"]+img+'.ctf.hed'

    cmd="applyctf %s %s parm=%f,200,1,0.1,0,17.4,9,1.53,%i,2,%f setparm flipphase" %(input,output,params["df"],params["kv"],params["apix"])
    print "phaseflipping",input

    f=os.popen(cmd)
    f.close()
    
def singleStack(params,img):
    if (params["phaseflip"]=='TRUE'):
        input=params["outdir"]+img+'.ctf.hed'
    else:
        input=params["outdir"]+img+'.hed'
    output=params["outdir"]+params["single"]
    
    singlepath=os.path.split(output)[0]

    # create output directory if it does not exist
    if (not os.path.exists(singlepath)):
        os.mkdir(singlepath)
           
    cmd="proc2d %s %s norm=0.0,1.0" %(input, output)
    
    # unless specified, invert the images
    if (params["noinvert"]=='FALSE'):
        cmd=cmd+" invert"

    # if specified, create spider stack
    if (params["spider"]=='TRUE'):
        cmd=cmd+" spiderswap"
    
    print "writing particles to stackfile: %s" %output
    # run proc2d & get number of particles
    f=os.popen(cmd)
    lines=f.readlines()
    f.close()
    for n in lines:
        words=n.split()
        if 'images' in words:
            count=int(words[-2])

    # create particle log file
    f=open(singlepath+'/.particlelog','a')
    out=''
    for n in range(count-params["particle"]):
        particlenum=str(1+n+params["particle"])
        line=str(particlenum)+'\t'+params["filepath"]+'/'+img+'.mrc'
        f.write(line+"\n")
    f.close()
    params["particle"]=count
    
    os.remove(params["outdir"]+img+".hed")
    os.remove(params["outdir"]+img+".img")
    if (params["phaseflip"]=='TRUE'):
        os.remove(params["outdir"]+img+".ctf.hed")
        os.remove(params["outdir"]+img+".ctf.img")

def writeBoxLog(commandline):
    f=open('.makestacklog','a')
    out=""
    for n in commandline:
        out=out+n+" "
    f.write(out)
    f.write("\n")
    f.close()
 
#-----------------------------------------------------------------------

if __name__ == '__main__':
    # record command line
    writeBoxLog(sys.argv)

    # parse command line input
    params=parseInput(sys.argv)

    # if making a single stack, remove existing stack if exists
    if (params["single"]!=''):
        stackfile=params["outdir"]+params["single"]
        if (os.path.exists(stackfile)):
            os.remove(stackfile)
        # set up counter for particle log
        p_logfile=params["outdir"]+'.particlelog'

        if (os.path.exists(p_logfile)):
            os.remove(p_logfile)
        params["particle"]=0
            
    # get list of input images, since wildcards are supported
    images=params["imgs"]

    # box particles
    # if any restrictions are set, check the image
    for img in images:
        # first remove any existing boxed files
        file=params["outdir"]+img
        if (os.path.exists(file+".hed") or os.path.exists(file+".img")):
            os.remove(file+".hed")
            os.remove(file+".img")

        params["hasace"]='FALSE'

        # get session ID
        params["filepath"]=getFilePath(img)

        # check if the image has been marked as good
        if (params["inspected"]!=''):
            goodimg=checkInspected(img)
            if (goodimg=='FALSE'):
                print img+".mrc has been rejected upon inspection"
                continue

        # check that ACE estimation is above confidence threshold
        if (params["ace"] != 0):
            # find ace values in database
            getAceValues(params,img)
            if (params["hasace"]=='FALSE'): 
                print img+".mrc has no ACE values"
                continue
            # if has ace values, see if above threshold
            goodimg=checkAce(img)
            if (goodimg=='FALSE'):
                print img+".mrc is below ACE threshold"
                continue

        # box the particles
        batchBox(params,img)
        if not(os.path.exists(params["outdir"]+img+".hed")):
            print "no particles were boxed from "+img+".mrc"
            continue
        
        # phase flip boxed particles if requested
        if (params["phaseflip"]=='TRUE'):
            getAceValues(params,img) # find ace values in database
            if (params["hasace"]=='FALSE'): 
                print img+".mrc has no ACE values"
                continue
            phaseFlip(params,img) # phase flip stack file

        # add boxed particles to a single stack
        if (params["single"]!=''):
            singleStack(params,img)
    print "Done!"
