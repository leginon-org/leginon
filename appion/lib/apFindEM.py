#FindEM specific options that will be depricated in the future

import os
import threading
import apDisplay
import apImage
import sys

#########################################################

class findemjob(threading.Thread):
   def __init__ (self, feed):
      threading.Thread.__init__(self)
      self.feed = feed
   def run(self):
		fin=''
		fin=os.popen('${FINDEM_EXE}','w')
		fin.write(self.feed)
		print "running findem.exe"
		fin.flush
		fin.close()

#########################################################

def runFindEM(imgname, params, thread=False):
	"""
	runs a separate thread of findem.exe for each template 
	to get cross-correlation maps
	"""
	os.chdir(params['rundir'])
	joblist = []
	ccmaplist = []

	if len(params['templatelist']) < 1:
		apDisplay.printError("templatelist == 0; there are no templates")

	for i in range(len(params['templatelist'])):
		classavg = i + 1

		#DETERMINE OUTPUT FILE NAME
		#CHANGE THIS TO BE 00%i in future
		#numstr = "%03d" % classavg
		numstr = str(classavg%10)+"00"
		ccmapfile="cccmaxmap"+numstr+".mrc"
		if (os.path.exists(ccmapfile)):
			os.remove(ccmapfile)

		#GET FINDEM RUN COMMANDS
		feed = findEMString(classavg, imgname, ccmapfile, params)

		#RUN THE PROGRAM
		apDisplay.printMsg("running findem.exe")
		if thread == True:
			current = findemjob(feed)
			joblist.append(current)
			current.start()
		else:
			fin=''
			fin=os.popen('${FINDEM_EXE}','w')
			fin.write(feed)
			fin.flush
			fin.close()

		#READ OUTPUT FILE
		if not os.path.exists(ccmapfile):
			apDisplay.printError("findem.exe did not run or crashed.\n"+
				"Did you source useappion.sh?")
		else:
			ccmaxmap = apImage.mrcToArray(ccmapfile)
			ccmaplist.append(ccmaxmap)

	if thread == True:
		for job in joblist:
			job.join()
	return ccmaplist


def findEMString(classavg, imgname, ccmapfile, params):

	#IMAGE INFO
	dwnimgname = os.path.splitext(imgname)[0]+".dwn.mrc"
	if not os.path.isfile(dwnimgname):
		apDisplay.printError("image file, "+dwnimgname+" was not found")
	else:
		print "image file, "+dwnimgname
	feed = dwnimgname+"\n"

	#TEMPLATE INFO
	tmpltroot = params["template"]
	if (len(params['templatelist'])==1 and not params['templateIds']):
		tmplname = tmpltroot+".dwn.mrc"
	else:
		tmplname = tmpltroot+str(classavg)+".dwn.mrc"

	if not os.path.exists(tmplname.strip()):
		apDisplay.printError("template file, "+tmplname+" was not found")
	else:
		print "template file, "+tmplname
	feed += tmplname + "\n"

	#DUMMY VARIABLE; DOES NOTHING
	feed += "-200.0\n"

	#BINNED APIX
	feed += str(params["apix"]*params["bin"])+"\n"

	#PARTICLE DIAMETER
	feed += str(params["diam"])+"\n"

	#RUN ID FOR OUTPUT FILENAME
	#numstr = "%03d" % classav
	numstr = str(classavg%10)+"00\n"
	feed += numstr

	#ROTATION PARAMETERS
	if params['multiple_range'] == True:
		strt = str(params["startang"+str(classavg)])
		end  = str(params["endang"+str(classavg)])
		incr = str(params["incrang"+str(classavg)])
	else:
		strt = str(params["startang"])
		end  = str(params["endang"])
		incr = str(params["incrang"])
	feed += strt+','+end+','+incr+"\n"

	#BORDER WIDTH
	borderwidth = str(int((params["diam"]/params["apix"]/params["bin"])/2)+1)
	feed += borderwidth+"\n"

	return feed
