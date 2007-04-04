#Future home of cross-correlation functions

def runCrossCorr(params,file):
	# Run Neil's version of FindEM
	#imagefile = file+".mrc"
	tmplt     =params["template"]

	image = process_image(imagefile,params)
	#print "Processed image Stats:"
	#imageinfo(image)

	#CYCLE OVER EACH TEMPLATE
	classavg=1
	blobs = []
	while classavg<=len(params['templatelist']):
		print "Template ",classavg
		outfile="cccmaxmap%i00.mrc" % classavg
		if (os.path.exists(outfile)):
			print " ... removing outfile:",outfile
			os.remove(outfile)

		if (params["multiple_range"]==True):
			strt=float(params["startang"+str(classavg)])
			end=float(params["endang"+str(classavg)])
			incr=float(params["incrang"+str(classavg)])
		else:
			strt=float(params["startang"])
			end=float(params["endang"])
			incr=float(params["incrang"])

		if (len(params['templatelist'])==1 and not params['templateIds']):
			templfile = tmplt+".mrc"
		else:
			templfile = tmplt+str(classavg)+".mrc"

		#MAIN FUNCTION HERE:
		blobs.append(getCrossCorrPeaks(image,file,templfile,classavg,strt,end,incr,params))

		classavg+=1
	
	numpeaks = mergePikFiles(file,blobs,params)

	del blobs

	return numpeaks
