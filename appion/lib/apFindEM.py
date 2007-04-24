#FindEM specific options that will be depricated in the future

import os
import threading
import apDisplay

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

def runFindEM(params, imgname, thread=False):
	"""
	runs a separate thread of findem.exe for each template 
	to get cross-correlation maps
	"""
	os.chdir(params['rundir'])
	tmplt=params["template"]
	numcls=len(params['templatelist'])
	pixdwn=str(params["apix"]*params["bin"])
	d=str(params["diam"])
	if (params["multiple_range"]==False):
		strt=str(params["startang"])
		end=str(params["endang"])
		incr=str(params["incrang"])
	border=str(int((params["diam"]/params["apix"]/params["bin"])/2)+1)
	joblist = []

	if len(params['templatelist']) < 1:
		apDisplay.printError("templatelist == 0; there are no templates")

	for i in range(len(params['templatelist'])):
		classavg = i + 1
		#OUTPUT
		cccfile="./cccmaxmap%i00.mrc" % classavg
		if (os.path.exists(cccfile)):
			os.remove(cccfile)

		#IMAGE INFO
		if (params['multiple_range']==True):
			strt=str(params["startang"+str(classavg)])
			end=str(params["endang"+str(classavg)])
			incr=str(params["incrang"+str(classavg)])
		dwnimgname = imgname+".dwn.mrc"
		if not os.path.isfile(dwnimgname):
			apDisplay.printError("image file, "+dwnimgname+" was not found")
		else:
			print "image file, "+dwnimgname
		feed = dwnimgname+"\n"

		#TEMPLATE INFO
		if (len(params['templatelist'])==1 and not params['templateIds']):
			tmplname = tmplt+".dwn.mrc\n"
		else:
			tmplname = tmplt+str(classavg)+".dwn.mrc\n"
		if not os.path.isfile(tmplname):
			apDisplay.printError("template file, "+tmplname+" was not found")
		else:
			print "template file, "+tmplname
		feed = feed+tmplname
		#DUMMY VARIABLE
		feed = feed+"-200.0\n"+pixdwn+"\n"+d+"\n"
		#RUN ID FOR OUTPUT FILENAME
		feed = feed+str(classavg)+"00\n"
		#ROTATION PARAMETERS
		feed = feed+strt+','+end+','+incr+"\n"
		#BORDER SIZE
		feed = feed+border+"\n"

		#RUN THE PROGRAM
		if thread == True:
			current = findemjob(feed)
			joblist.append(current)
			current.start()
		else:
			fin=''
			fin=os.popen('${FINDEM_EXE}','w')
			fin.write(feed)
			print "running findem.exe"
			fin.flush
			fin.close()	

		if not os.path.exists(cccfile):
			apDisplay.printError("findem.exe did not run or crashed.\n"+
				"Did you source useappion.sh?")

	for job in joblist:
		job.join()
	return []
