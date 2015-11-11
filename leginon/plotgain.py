#!/usr/bin/env python

import sinedon
from matplotlib import pyplot as plt
from pyami import mrc
import leginon.leginondata as leginondata
import os
import argparse

def parseArguments():
	parser=argparse.ArgumentParser(description='Plot recent gain reference data')
	parser.add_argument('n', metavar='n', type=int, help='number of images to analyze')
	parser.add_argument('-b', metavar='b', type=int, help='binning of gains to analyze')
	parser.add_argument('-x', metavar='x', type=int, help='x dimension of gains to analyze (3840 for DE20 binned by 1)')
	parser.add_argument('-y', metavar='y', type=int, help='y dimension of gains to analyze (5120 for DE20 binned by 1)')
	args=parser.parse_args()	
	return args

def getGainInfo(gaindata,totalimages):
	meanlst=[]
	stdlst=[]
	timelst=[]
	templst=[]
	gaindict={}
	print "collecting image information"
	count=0
	for imgdata in gaindata[-1*totalimages:]:
		count+=1
		if count%10==0:
			print "image %d of %d" % (count,totalimages)
		refpath=imgdata['session']['image path']
		refname=imgdata['filename']+'.mrc'
		ref=os.path.join(refpath,refname)
		
		try:
			img=mrc.read(ref)
			mean=img.mean()
			meanlst.append(mean)
	
			std=img.std()
			stdlst.append(std)
		
			time=imgdata.timestamp
			timelst.append(time)
			
			temp=imgdata['camera']['temperature']
			templst.append(temp)

		except:
			print "no data found for %s" % ref
	gaindict['meanlst']=meanlst
	gaindict['stdlst']=stdlst
	gaindict['timelst']=timelst
	gaindict['templst']=templst
	
	return gaindict

if __name__ == '__main__':
	
	args=parseArguments()
	totalimages=args.n
	sinedon.setConfig('leginondata')

	darkq=leginondata.DarkImageData()
	camq=leginondata.CameraEMData()
	camq['binning']={'y':long(args.b),'x':long(args.b)}
	camq['dimension']={'y': long(args.y), 'x': long(args.x)}
	darkq['camera']=camq
	print "querying dark images"
	darkdata=darkq.query(results=totalimages)
	darkdata.reverse()
	darkd=getGainInfo(darkdata,totalimages)
	
	brightq=leginondata.BrightImageData()
	brightq['camera']=camq
	print "querying bright images"
	brightdata=brightq.query(results=totalimages)
	brightdata.reverse()
	brightd=getGainInfo(brightdata,totalimages)

	fig_base=plt.figure()
	fig1=fig_base.add_subplot(111)
	plt.grid(True)
	
	#l1=fig1.errorbar(timelst,meanlst, 'bo', label='Dark mean', yerr=stdlst)
	fig1.plot(brightd['timelst'],brightd['meanlst'], 'rv', label='Bright mean')
	fig1.plot(darkd['timelst'],darkd['meanlst'], 'bo', label='Dark mean')
	plt.xlabel('Date/Time')
	plt.ylabel('Mean intensity')
	plt.gca().set_ylim(ymin=0.0)
	
	fig2=fig1.twinx()
	fig2.plot(darkd['timelst'], darkd['templst'], 'g--', label='Temperature')
	plt.ylabel('Temperature')
	plt.gca().set_ylim(ymin=-50.0, ymax=-20)
	
	h1,l1=fig1.get_legend_handles_labels()
	h2,l2=fig2.get_legend_handles_labels()
	fig1.legend(h2+h1,l2+l1,loc='upper right', frameon=False, fontsize=10)

	#pyplot.plot(timelst,meanlst,'bo')
	plt.show()