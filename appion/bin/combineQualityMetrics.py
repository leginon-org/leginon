#!/usr/bin/env python

''' 
metric combiner for common lines final model evaluation. Takes as input a statistics file, with 
header description for each columns, outputs a statistics file, sorted according to the combined 
metrics
'''

from appionlib import apCommonLines
from optparse import OptionParser
from appionlib import apDisplay

def setupParserOptions():

	### filename option
	usage = "usage: %prog --infile=filename --outfile=filename "
	usage+= "--metrics='metric1,weight,sign metric2,weight,sign' ... ; where sign is 1 or -1"
	parser = OptionParser(usage)
	parser.add_option("--infile", dest="infile", help="name of file with original statistics", 
		metavar="FILE")
	parser.add_option("--outfile", dest="outfile", help="name of output file", metavar="FILE")
	parser.add_option("--metrics", dest="metrics", help="list of metrics with corresponding weight \
		and sign value, comma separated. An example is: --metrics=='CCPR,1,1 EJ,0.5,-1 FSC,0.1,-1'. \
		The first value is the name of the metric, as it appears in the above filename; \
		the second value is the weight given to the metric; the third value is the sign, \
		specified as 1 or -1, depending on whether the value should be maximized or minimized",
		metavar="STR")
	return parser.parse_args()
	
def checkConflicts(options, args):	
	
	### metrics with values
	if options.infile == None:
		errmsg = "specify the input filename with quality metrics and associated values "
		errmsg+= "e.g. --infile=final_model_stats.dat"
		apDisplay.printError(errmsg)
	if options.outfile == None:
		errmsg = "specify the output filename with quality metrics and associated values "
		errmsg+= "e.g. --outfile=final_model_stats_sorted_by_Rcrit.dat"
		apDisplay.printError(errmsg)
	if options.metrics == None: 
		errmsg = "please specify the desired metric(s) to combine, along with appropriate "
		errmsg+= "weight and sign, for example: --metrics='CCPR,1,1 EJ,0.5,-1 FSC,0.1,-1'"
		apDisplay.printError(errmsg)
	return

##########################
	
if __name__ == "__main__":
	options, args = setupParserOptions()
	checkConflicts(options, args)
	metrics = options.metrics.split()
	kwargs = {}
	for metric in metrics:
		m, weight, sign = metric.split(",")
		kwargs[m] = (float(weight),int(sign))
	apCommonLines.combineMetrics(options.infile, options.outfile, **kwargs)