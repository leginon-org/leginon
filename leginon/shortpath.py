#!/usr/bin/env python

import random
import sys
from optparse import OptionParser
import os
from PIL import Image, ImageDraw, ImageFont
from math import sqrt, hypot
import numpy
import logging

def hillclimb(init_function,move_operator,objective_function,max_evaluations):
	'''
	hillclimb until either max_evaluations is reached or we are at a local optima
	'''
	best=init_function()
	best_score=objective_function(best)
	
	num_evaluations=1
	
	logging.info('hillclimb started: score=%f',best_score)
	
	while num_evaluations < max_evaluations:
		# examine moves around our current position
		move_made=False
		for next in move_operator(best):
			if num_evaluations >= max_evaluations:
				break
			
			# see if this move is better than the current
			next_score=objective_function(next)
			num_evaluations+=1
			if next_score > best_score:
				best=next
				best_score=next_score
				move_made=True
				break # depth first search
			
		if not move_made:
			break # we couldn't find a better move (must be at a local maximum)
	
	logging.info('hillclimb finished: num_evaluations=%d, best_score=%f',num_evaluations,best_score)
	return (num_evaluations,best_score,best)

def hillclimb_and_restart(init_function, move_operator, objective_function, max_iterations, max_evaluations):
	'''
	repeatedly hillclimb until max_evaluations is reached
	'''
	best=None
	best_score=0
	
	num_evaluations=0
	num_iterations=0
	while num_iterations < max_iterations:
		num_iterations+=1
		logging.info('(re)starting hillclimb %d/%d remaining', num_iterations, max_iterations)
		evaluated, score, found=hillclimb(init_function, move_operator, objective_function, max_evaluations)
		num_evaluations+=evaluated

		if score > best_score or best is None:
			best_score=score
			best=found
		
	return (num_evaluations, best_score, best)


def all_pairs(size,shuffle=random.shuffle):
	'''generates all i,j pairs for i,j from 0-size uses shuffle to randomise (if provided)'''
	r1=range(size)
	r2=range(size)
	if shuffle:
		shuffle(r1)
		shuffle(r2)
	for i in r1:
		for j in r2:
			yield (i,j)

def reversed_sections(tour):
	'''generator to return all possible variations where the section between two cities are swapped'''
	for i,j in all_pairs(len(tour)):
		if i != j:
			copy=tour[:]
			if i < j:
				copy[i:j+1]=reversed(tour[i:j+1])
			else:
				copy[i+1:]=reversed(tour[:j])
				copy[:j]=reversed(tour[i+1:])
			if copy != tour: # no point returning the same tour
				yield copy

def swapped_cities(tour):
	'''generator to create all possible variations where two cities have been swapped'''
	for i,j in all_pairs(len(tour)):
		if i < j:
			copy=tour[:]
			copy[i],copy[j]=tour[j],tour[i]
			yield copy

def shift_cities(tour):
	'''generator to create all possible variations where two cities have been swapped'''
	for i,j in all_pairs(len(tour)):
		if i != j:
			copy = tour[0:i]
			copy.extend(tour[i+1:j])
			copy.append(tour[i])
			copy.extend(tour[j:len(tour)])
			yield copy

def cartesian_matrix(coords):
	'''create a distance matrix for the city coords that uses straight line distance'''
	matrix={}
	for i,(x1,y1) in enumerate(coords):
		for j,(x2,y2) in enumerate(coords):
			dx,dy=x1-x2,y1-y2
			dist = hypot(dx, dy)
			#dist=sqrt(dx*dx + dy*dy)
			matrix[i,j]=dist
	return matrix

def read_coords(coord_file):
	'''
	read the coordinates from file and return the distance matrix.
	coords should be stored as comma separated floats, one x,y pair per line.
	'''
	coords=[]
	for line in coord_file:
		x,y=line.strip().split(',')
		coords.append((float(x),float(y)))
	return coords

def tour_length1(matrix,tour):
	'''total up the total length of the tour based on the distance matrix'''
	total=0
	try:
		num_cities=len(tour)
	except:
		print "Could not get len of tour"
		print type(tour)
		print "Tour=",tour
		return 1.0e10
	for i in range(num_cities-1):
		city_i=tour[i]
		city_j=tour[i+1]
		total+=matrix[city_i,city_j]
	return total

def tour_length2(matrix,tour):
	'''total up the total length of the tour based on the distance matrix'''
	total=0
	try:
		num_cities=len(tour)
	except:
		print "Could not get len of tour"
		print type(tour)
		print "Tour=",tour
		return 1.0e10
	for i in range(num_cities):
		j=(i+1)%num_cities
		city_i=tour[i]
		city_j=tour[j]
		total+=matrix[city_i,city_j]
	return total

def write_tour_to_img(coords,tour,title,img_file):
	padding=20
	# shift all coords in a bit
	coords=[(x+padding,y+padding) for (x,y) in coords]
	maxx,maxy=0,0
	for x,y in coords:
		maxx=max(x,maxx)
		maxy=max(y,maxy)
	maxx+=padding
	maxy+=padding
	img=Image.new("RGB",(int(maxx),int(maxy)),color=(255,255,255))
	
	font=ImageFont.load_default()
	d=ImageDraw.Draw(img);
	num_cities=len(tour)
	for i in range(num_cities):
		j=(i+1)%num_cities
		city_i=tour[i]
		city_j=tour[j]
		x1,y1=coords[city_i]
		x2,y2=coords[city_j]
		d.line((int(x1),int(y1),int(x2),int(y2)),fill=(0,0,0))
		d.text((int(x1)+7,int(y1)-5),str(i),font=font,fill=(32,32,32))
	
	
	for x,y in coords:
		x,y=int(x),int(y)
		d.ellipse((x-5,y-5,x+5,y+5),outline=(0,0,0),fill=(196,196,196))
	
	d.text((1,1),title,font=font,fill=(0,0,0))
	
	del d
	img.save(img_file, "PNG")

def init_random_tour(tour_length):
	tour=range(tour_length)
	random.shuffle(tour)
	return tour

def run_hillclimb(init_function, move_operator, objective_function, max_iterations, max_evaluations):
	evalutions, score, best = hillclimb_and_restart(init_function, move_operator,
		objective_function, max_iterations, max_evaluations)
	return evalutions, score, best

def convertParserToParams(parser):
	parser.disable_interspersed_args()
	(options, args) = parser.parse_args()
	if len(args) > 0:
		apDisplay.printError("Unknown commandline options: "+str(args))
	if len(sys.argv) < 2:
		parser.print_help()
		parser.error("no options defined")

	params = {}
	for i in parser.option_list:
		if isinstance(i.dest, str):
			params[i.dest] = getattr(options, i.dest)
	return params

def setupOptParse():
	usage = ("Usage: %prog [-o <output png image file>] [-v] "
		+"[-m reverse_sections|swap_cities] -n <max iterations> "
		+"-e <max evaluations> -c <coord file>")
	parser = OptionParser(usage=usage)
	parser.add_option("-v", "--verbose", dest="verbose", default=False,
		action="store_true", help="Print verbsoe log messages")
	parser.add_option("-o", "--output-image", dest="outfilename",
		help="Output PNG image", metavar="FILE")
	parser.add_option("-n", "--num-iter", dest="num_iter", type="int", default=5,
		help="Number of iterations", metavar="INT")
	parser.add_option("-e", "--max-eval", dest="max_eval", type="int", default=70000,
		help="Maximum number of evaluations per iteration", metavar="INT")
	parser.add_option("-m", "--move-oper", dest="move_operator",
		help="Move operation, either 'swapped_cities' or 'reversed_sections'", metavar="METHOD", 
		type="choice", choices=("swapped_cities","reversed_sections"), default="reversed_sections" )
	parser.add_option("-c", "--coord-file", dest="city_file",
		help="File containing coordinates to optimize", metavar="FILE" )
	params = convertParserToParams(parser)

	if params['outfilename'] and not params['outfilename'].endswith(".png"):
		parser.print_help()
		parser.error("output image file name must end in .png")

	if not params['city_file'] and not os.path.isfile(params['city_file']):
		parser.print_help()
		parser.error("could not find file: "+str(params['city_file']))

	if params['move_operator'] == 'swapped_cities':
		params['move_operator'] = swapped_cities
	elif params['move_operator'] == 'reversed_sections':
		params['move_operator'] = reversed_sections
	else:
		params['move_operator'] = reversed_sections

	return params


def sortPoints(coords, numiter=3, maxeval=70000, writepng=False, msg=False):
	"""
	inputs:
		list of coordinates
		num of iterations
		max evaluations per iteration
	outputs:
		list of numbers that correlation to new order
		total distance
	"""

	if not coords or len(coords) < 2:
		return range(len(coords)), 0.0

	#setup starting order
	#startorder = lambda: init_random_tour(len(coords)) #random
	startorderfunc = lambda: range(len(coords)) #ordered
	bestorder = startorderfunc()
	#print "startorder=",startorderfunc()

	#setup distance matrix
	matrix = cartesian_matrix(coords)
	startscore = -tour_length1(matrix, startorderfunc())
	#print "beginning distance="+str(round(-1*startscore,2))+" pixels"
	bestscore = startscore

	#setup fitness function: total distance
	fitnessfunc = lambda tour: -tour_length1(matrix, tour)

	#print "###################"
	#print "reversed sections"
	#print "###################"
	method = reversed_sections
	for i in range(numiter):
		iters, score, order = run_hillclimb(startorderfunc, method, fitnessfunc, 1, maxeval)
		if score > bestscore:
			#print "new best score:", score
			bestiters = iters
			bestscore = score
			bestorder = order	
			if writepng is True:
				outfile = str(int(abs(score)))+".png"
				write_tour_to_img(coords, order, str(score), file(outfile,'w'))

	#print "###################"
	#print "shift cities"
	#print "###################"
	method = shift_cities
	for i in range(2):
		startorderfunc = lambda: bestorder
		iters, score, order = run_hillclimb(startorderfunc, method, fitnessfunc, 1, maxeval)
		if score > bestscore:
			#print "new best score:", score
			bestiters = iters
			bestscore = score
			bestorder = order
			if writepng is True:
				outfile = str(int(abs(score)))+".png"
				write_tour_to_img(coords, order, str(score), file(outfile,'w'))

	percent = 100.0 * abs(startscore - bestscore) / abs(startscore)
	messages = []
	messages.append( "shortened distance from "+str(round(-1*startscore,2))+" to "
		+str(round(-1*bestscore,2))+" pixels ("+str(round(percent,2))+"% shorter)" )
	bestarray = numpy.asarray(bestorder, dtype=numpy.int32)
	messages.append("best order="+str(bestarray+1))
	if msg is True:
		print message
	return bestorder, bestscore, messages


##########################################
##########################################
def main():
	params = setupOptParse()
	import logging
	format='%(asctime)s %(levelname)s %(message)s'
	if params['verbose']:
		logging.basicConfig(level=logging.INFO,format=format)
	else:
		logging.basicConfig(format=format)
	
	# setup the things tsp specific parts hillclimb needs
	origcoords = read_coords(file(params['city_file']))
	bestorder, bestscore = sortPoints(origcoords, params['num_iter'], params['max_eval'])

	if params['outfilename']:
		write_tour_to_img(origcoords, bestorder, '%s: %f'%(params['city_file'], bestscore), file(params['outfilename'],'w'))

if __name__ == "__main__":
	main()
