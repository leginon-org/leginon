#!/usr/bin/env python

from subprocess import Popen, PIPE
import sys
command = ' '.join(sys.argv[1:-4])
sys.stdout.write("Run: "+command+"\n")
p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
output, err = p.communicate()
if err:
    sys.stderr.write(err)
else:
    sys.stdout.write(output)
if sys.argv[2] != 'extract': sys.exit()
from appionlib import apDatabase
from appionlib import apParticle
from appionlib import apProject
from appionlib import appionScript
from appionlib import appiondata
from leginon import leginondata

from appionlib import apParam
import os, csv
break_item = False
for item in sys.argv:
    if break_item: break
    if item.startswith("--output"):
        break_item= True
particles = item
basedir =  os.path.split(particles)[0]
preprocessed = os.path.join(basedir, "preprocessed")
prep = os.path.join(preprocessed, 'preprocessed.appionsub.job')

txt = open(prep).read()
scale = float(txt.split('--scale')[1].split()[0])
train = os.path.join(basedir, "train", 'train.appionsub.job')
txt = open(train).read()
radius = float(txt.split('--radius')[1].split()[0])
diameter = 2*radius*scale
reader = csv.reader(open(particles), delimiter='\t')
next(reader)
imageDict = {}
for row in reader:
    peakdict = {
                    'diameter': diameter,
                    'xcoord': float(row[1])*scale,
                    'ycoord': float(row[2])*scale,
                    'peakarea': row[3]
                }        
    if row[0] in imageDict:
        imageDict[row[0]].append(peakdict)
    else:
        imageDict[row[0]] = [peakdict]
for item in sys.argv:
    if item.startswith("--expid"):
        expid = item[8:]
    elif item.startswith("--projectid"):
        projectid = item[12:]
        
sessiondata = apDatabase.getSessionDataFromSessionId(expid)
apProject.setDBfromProjectId(projectid)
pathdata = appiondata.ApPathData(path=preprocessed)
runq = appiondata.ApSelectionRunData()
runname = "topaz"+apParam.makeTimestamp()
runq['name'] = runname
runq['session'] = sessiondata
runq['program'] = "Topaz"
runq['path'] = pathdata
runq.insert()

for filename in imageDict:
    imgquery = leginondata.AcquisitionImageData(filename=filename)
    imgres = imgquery.query(readimages=False, results=1)
    imgdata = imgres[0]
    apParticle.fastInsertParticlePeaks(imageDict[filename], imgdata, runname, msg=True)
