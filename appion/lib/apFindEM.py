#FindEM specific options that will be depricated in the future

import os
import threading
import apDisplay

def runFindEM(params,file):
	"""
	runs findem.exe to get cross-correlation map
	"""
	tmplt=params["template"]
	numcls=len(params['templatelist'])
	pixdwn=str(params["apix"]*params["bin"])
	d=str(params["diam"])
	if (params["multiple_range"]==False):
		strt=str(params["startang"])
		end=str(params["endang"])
		incr=str(params["incrang"])
	bw=str(int((params["diam"]/params["apix"]/params["bin"])/2)+1)

	classavg=1
	while classavg<=len(params['templatelist']):
		# first remove the existing cccmaxmap** file
		cccfile="cccmaxmap%i00.mrc" %classavg
		if (os.path.exists(cccfile)):
			os.remove(cccfile)

		if (params["multiple_range"]==True):
			strt=str(params["startang"+str(classavg)])
			end=str(params["endang"+str(classavg)])
			incr=str(params["incrang"+str(classavg)])
		fin='';
		#fin=os.popen('${FINDEM_PATH}/FindEM_SB','w')
		fin=os.popen('${FINDEM_EXE}','w')
		fin.write(file+".dwn.mrc\n")
		if (len(params['templatelist'])==1 and not params['templateIds']):
			fin.write(tmplt+".dwn.mrc\n")
		else:
			fin.write(tmplt+str(classavg)+".dwn.mrc\n")
		fin.write("-200.0\n")
		fin.write(pixdwn+"\n")
		fin.write(d+"\n")
		fin.write(str(classavg)+"00\n")
		fin.write(strt+','+end+','+incr+"\n")
		fin.write(bw+"\n")
		print "running findem.exe"
		fin.flush
		fin.close()

		if (not os.path.exists(cccfile)):
			apDisplay.printError("findem.exe did not run or crashed.\n"+
				"Did you source useappion.sh?")

		classavg+=1
	#return Mrc.Mrc_to_numeric("cccmaxmap%i00.mrc")
	return

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

def threadFindEM(params,file):
	"""
	runs a separate thread of findem.exe for each template 
	to get cross-correlation maps
	"""
	tmplt=params["template"]
	numcls=len(params['templatelist'])
	pixdwn=str(params["apix"]*params["bin"])
	d=str(params["diam"])
	if (params["multiple_range"]==False):
		strt=str(params["startang"])
		end=str(params["endang"])
		incr=str(params["incrang"])
	bw=str(int((params["diam"]/params["apix"]/params["bin"])/2)+1)
	joblist = []

	classavg=1
	while classavg<=len(params['templatelist']):
		cccfile="./cccmaxmap%i00.mrc" % classavg
		if (os.path.exists(cccfile)):
			os.remove(cccfile)

		if (params["multiple_range"]==True):
			strt=str(params["startang"+str(classavg)])
			end=str(params["endang"+str(classavg)])
			incr=str(params["incrang"+str(classavg)])

		feed = file+".dwn.mrc\n"
		if (len(params['templatelist'])==1 and not params['templateIds']):
			feed = feed+tmplt+".dwn.mrc\n"
		else:
			feed = feed+tmplt+str(classavg)+".dwn.mrc\n"
		feed = feed+"-200.0\n"+pixdwn+"\n"+d+"\n"
		feed = feed+str(classavg)+"00\n"
		feed = feed+strt+','+end+','+incr+"\n"
		feed = feed+bw+"\n"
		current = findemjob(feed)
		joblist.append(current)
		current.start()
		classavg+=1

	for job in joblist:
		job.join()
	return
