import numpy
import operator

def combineMetrics(statfilename, outfile, **kwargs):
        ''' 
        takes all calculated metrics and combines them into a single Rcrit value, according to:
        Rossmann, M. G., et al. (2001). "Combining electron microscopic with x-ray crystallographic structures." J Struct Biol 136(3): 190-200.
        metrics are combined as follows: 
        
        Rcrit = sum(weight[i] * sign[i] * ((v[i] - mean(v)) / (stdev(v)))) * sqrt(sum(weight[i])), where: 
        weight is a weight for each given criterion, 
        v is the criterion used to evaluate data,
        sign is (+/-)1, depending on whether the criterion has to be minimized or maximized

	*** the more general case: each keyword argument is a dictionary, where key=name of metric, value=(weight of metric, sign of metric)
	'''

	### read data
	f = open(statfilename, "r")
	flines = f.readlines()
	fnames = flines[0]
	fvals = flines[1:]
	f.close()
	mnames_split = fnames.strip().split()
	vals_split = [line.strip().split() for line in fvals]

	### model names
	names = []
	for list in vals_split:
		names.append(str(list[0]))

	### set value lists
	toEvaluate = {}
	list_names = {}
	for key, value in kwargs.iteritems():
		toEvaluate[key] = {"weight": value[0], "sign": value[1], "vals": []}
		for i, name in enumerate(mnames_split):
			if name == key:
				list_names[key] = i
	for name, index in list_names.iteritems():
		for l in vals_split:
			toEvaluate[name]['vals'].append(float(l[index]))

	### output should be sorted according to the weights
	sorted_metrics = sorted(kwargs.iteritems(), key=operator.itemgetter(1), reverse=True)
#	print "using the following criteria to evaluate Rcrit: ", sorted_metrics 

	### for each model, evaluate Rcrit based on all selected criteria
	Rcritdict1 = {} # for sorting only
	Rcritdict2 = {}
	weightsum = 0
	for valnames, allvals in toEvaluate.iteritems():
		weight = allvals['weight']
		weightsum += abs(weight)
	for i in range(len(fvals)):
		Rcrit = 0
		Rcritdict2[names[i]] = {}
		for valname, allvals in toEvaluate.iteritems():
			weight = allvals['weight']
			sign = allvals['sign']
			vals = allvals['vals']
			if float(numpy.std(vals)) == 0.0:
				std = 1
			else:
				std = numpy.std(vals)
			R = weight * sign * ((vals[i] - numpy.mean(vals)) / std) / weightsum
			Rcrit += R
			Rcritdict2[names[i]][valname] = vals[i] 
		Rcritdict1[names[i]] = Rcrit

	### write out values, sorted by Rcrit
	sorted_Rcritlist = sorted(Rcritdict1.iteritems(), key=operator.itemgetter(1))
	sorted_Rcritlist.reverse()
	f = open(outfile, "w")
	f.write("%11s %9s " % ("MODEL", "RCRIT"))
	for m in sorted_metrics:
		f.write("%9s " % m[0])
	f.write("\n")
	for i in range(len(sorted_Rcritlist)):
		d = Rcritdict2[sorted_Rcritlist[i][0]]
		f.write("%11s %9.4f " % (sorted_Rcritlist[i][0], Rcritdict1[sorted_Rcritlist[i][0]]))
		for m in sorted_metrics:
			f.write("%9.4f " % d[m[0]])
		f.write("\n")
	f.close()
	

def combineMetrics1(N=False, wN=1, CCPR=True, wCCPR=1, EJ=True, wEJ=1, CCC=False, wCCC=1, STDEV=False, wSTDEV=1, SSNR=True, wSSNR=1):
	''' 
	takes all calculated metrics and combines them into a single Rcrit value, according to:
	Rossmann, M. G., et al. (2001). "Combining electron microscopic with x-ray crystallographic structures." J Struct Biol 136(3): 190-200.
	metrics are combined as follows: 
	
	Rcrit = sum(weight[i] * sign[i] * ((v[i] - mean(v)) / (stdev(v)))) * sqrt(sum(weight[i])), where: 
	weight is a weight for each given criterion, 
	v is the criterion used to evaluate data,
	sign is (+/-)1, depending on whether the criterion has to be minimized or maximized
	'''
	
	### read data
	f = open("final_model_stats.dat", "r")
	flines = f.readlines()[1:]
	f.close()
	strip = [line.strip() for line in flines]
	split = [line.split() for line in strip]
	
	### set value lists
	toEvaluate = {}
	names = []
	Ns = []
	CCPRs = []
	EJs = []
	CCCs = []
	STDEVs = []
	SSNRs = []
	if N is True:			### number of models
		toEvaluate["N"] = {"weight": wN, "sign": 1, "vals": Ns}
	if CCPR is True:		### cross-correlation b/w projections & reprojections
		toEvaluate["CCPR"] = {"weight": wCCPR, "sign": 1, "vals": CCPRs}
	if EJ is True:			### average Euler jump
		toEvaluate["EJ"] = {"weight": wEJ, "sign": -1, "vals": EJs}
	if CCC is True:			### avg CCC within the model class
		toEvaluate["CCC"] = {"weight": wCCC, "sign": 1, "vals": CCCs}
	if STDEV is True:		### avg stdev of CCC within the model class
		toEvaluate["STDEV"] = {"weight": wSTDEV, "sign": -1, "vals": STDEVs}
	if SSNR is True:		### SSNR of the model class
		toEvaluate["SSNR"] = {"weight": wSSNR, "sign": -1, "vals": SSNRs}
		
	for list in split:
		### put all relevant parameters to list
		names.append(str(list[0]))
		Ns.append(int(float(list[1])))			
		CCPRs.append(float(list[2]))
		EJs.append(float(list[3]))
		CCCs.append(float(list[4]))
		STDEVs.append(float(list[5]))
		SSNRs.append(float(list[6]))	
			
	### for each model, evaluate Rcrit based on all selected criteria
	print "using the following criteria to evaluate Rcrit: ", toEvaluate.keys()
	Rcritdict1 = {}
	Rcritdict2 = {}
	weightsum = 0
	for valnames, allvals in toEvaluate.iteritems():
		weight = allvals['weight']
		weightsum += weight
	for i in range(len(names)):
		Rcrit = 0
		for valname, allvals in toEvaluate.iteritems():
			weight = allvals['weight']
			sign = allvals['sign']
			vals = allvals['vals']
			R = weight * sign * ((vals[i] - numpy.mean(vals)) / (numpy.std(vals))) / weightsum
			Rcrit += R
		Rcritdict1[names[i]] = Rcrit
		Rcritdict2[names[i]] = \
			{"Rcrit":Rcrit, "Mnum":names[i], "N":Ns[i], "CCPR":CCPRs[i], "EJ":EJs[i], "CCC":CCCs[i], "STDEV":STDEVs[i], "SSNR":SSNRs[i]}
	
	### write out values, sorted by Rcrit
	f = open("final_model_stats_sorted_by_Rcrit.dat", "w")
	f.write("%9s %8s %5s %8s %8s %8s %8s %8s\n" \
		% ("MODEL", "RCRIT", "NUM", "CCPR", "EJ", "CCC", "STDEV", "SSNR"))
	sorted_Rcritlist = sorted(Rcritdict1.iteritems(), key=operator.itemgetter(1))
	sorted_Rcritlist.reverse()
	for i in range(len(sorted_Rcritlist)):
		d = Rcritdict2[sorted_Rcritlist[i][0]]
		f.write("%9s %8.4f %5d %8.3f %8.3f %8.3f %8.3f %8.3f\n" \
			% (d['Mnum'], d['Rcrit'], d['N'], d['CCPR'], d['EJ'], d['CCC'], d['STDEV'], d['SSNR']))
	f.close()
	
	return

#=====================
#=====================
#=====================	

def combineMetrics2(N=False, wN=1, CCPR=True, wCCPR=1, EJ=True, wEJ=1, CCC=False, wCCC=1, STDEV=False, wSTDEV=1, FSC=True, wFSC=1):
	''' 
	takes all calculated metrics and combines them into a single Rcrit value, according to:
	Rossmann, M. G., et al. (2001). "Combining electron microscopic with x-ray crystallographic structures." J Struct Biol 136(3): 190-200.
	metrics are combined as follows: 
	
	Rcrit = sum(weight[i] * sign[i] * ((v[i] - mean(v)) / (stdev(v)))) * sqrt(sum(weight[i])), where: 
	weight is a weight for each given criterion, 
	v is the criterion used to evaluate data,
	sign is (+/-)1, depending on whether the criterion has to be minimized or maximized
	'''
	
	### read data
	f = open("final_model_stats.dat", "r")
	flines = f.readlines()[1:]
	f.close()
	strip = [line.strip() for line in flines]
	split = [line.split() for line in strip]
	
	### set value lists
	toEvaluate = {}
	names = []
	Ns = []
	CCPRs = []
	EJs = []
	CCCs = []
	STDEVs = []
	FSCs = []
	if N is True:			### number of models
		toEvaluate["N"] = {"weight": wN, "sign": 1, "vals": Ns}
	if CCPR is True:		### cross-correlation b/w projections & reprojections
		toEvaluate["CCPR"] = {"weight": wCCPR, "sign": 1, "vals": CCPRs}
	if EJ is True:			### average Euler jump
		toEvaluate["EJ"] = {"weight": wEJ, "sign": -1, "vals": EJs}
	if CCC is True:			### avg CCC within the model class
		toEvaluate["CCC"] = {"weight": wCCC, "sign": 1, "vals": CCCs}
	if STDEV is True:		### avg stdev of CCC within the model class
		toEvaluate["STDEV"] = {"weight": wSTDEV, "sign": -1, "vals": STDEVs}
	if FSC is True:		### FSC of the model class
		toEvaluate["FSC"] = {"weight": wFSC, "sign": -1, "vals": FSCs}
		
	for list in split:
		### put all relevant parameters to list
		names.append(str(list[0]))
		Ns.append(int(float(list[1])))			
		CCPRs.append(float(list[2]))
		EJs.append(float(list[3]))
		CCCs.append(float(list[4]))
		STDEVs.append(float(list[5]))
		FSCs.append(float(list[6]))	
			
	### for each model, evaluate Rcrit based on all selected criteria
	print "using the following criteria to evaluate Rcrit: ", toEvaluate.keys()
	Rcritdict1 = {}
	Rcritdict2 = {}
	weightsum = 0
	for valnames, allvals in toEvaluate.iteritems():
		weight = allvals['weight']
		weightsum += weight
	for i in range(len(names)):
		Rcrit = 0
		for valname, allvals in toEvaluate.iteritems():
			weight = allvals['weight']
			sign = allvals['sign']
			vals = allvals['vals']
			R = weight * sign * ((vals[i] - numpy.mean(vals)) / (numpy.std(vals))) / weightsum
			Rcrit += R
		Rcritdict1[names[i]] = Rcrit
		Rcritdict2[names[i]] = \
			{"Rcrit":Rcrit, "Mnum":names[i], "N":Ns[i], "CCPR":CCPRs[i], "EJ":EJs[i], "CCC":CCCs[i], "STDEV":STDEVs[i], "FSC":FSCs[i]}
	
	### write out values, sorted by Rcrit
	f = open("final_model_stats_sorted_by_Rcrit.dat", "w")
	f.write("%11s %8s %5s %8s %8s %8s %8s %8s\n" \
		% ("MODEL", "RCRIT", "NUM", "CCPR", "EJ", "CCC", "STDEV", "FSC"))
	sorted_Rcritlist = sorted(Rcritdict1.iteritems(), key=operator.itemgetter(1))
	sorted_Rcritlist.reverse()
	for i in range(len(sorted_Rcritlist)):
		d = Rcritdict2[sorted_Rcritlist[i][0]]
		f.write("%11s %8.4f %5d %8.3f %8.3f %8.3f %8.3f %8.3f\n" \
			% (d['Mnum'], d['Rcrit'], d['N'], d['CCPR'], d['EJ'], d['CCC'], d['STDEV'], d['FSC']))
	f.close()
	
	return

