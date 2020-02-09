#!/usr/bin/env python
#-----------------------
# change these for your testing
#-----------------------
# import the module of your scope
#from pyscope import fei
from pyscope import simtem
# create instance of this tem
#c = fei.Glacios()
c = simtem.SimTEM300()
# alpha angle to move in degrees
delta_angle = 60.0
# repeet test and average
repeats = 1
#------------------------
# no change required below
#------------------------
import time

def testTiltSpeed(tem_obj, delta_angle, speed):
	display_scale = 180.0/3.14159
	display_unit = 'degrees'
	distance = delta_angle / display_scale

	functionname = 'StagePosition'
	getfunc = getattr(tem_obj,'get'+functionname)
	setfunc = getattr(tem_obj,'set'+functionname)

	p0 = getfunc()


	move_times = []
	calc_time = delta_angle / speed
	print '-----'
	print 'expected time for %.2f degrees/sec is\t %8.3f seconds' % (speed, calc_time)
	for i in range(repeats):
		for d in (distance,):
			tem_obj.setStageSpeed(speed) # degrees per second
			p = getfunc()
			p1 = {'a':p['a']+d}
			t0 = time.time()
			setfunc(p1)
			t1 = time.time()
			move_time = t1 - t0
			print '%s by %.2f %s took\t %8.3f seconds' % (functionname, d*display_scale, display_unit, move_time)
			move_times.append(move_time)
			time.sleep(3.0)
			# reset back to the original
			tem_obj.resetStageSpeed()
			setfunc(p0)
			time.sleep(0.5)
	avg_move_time = sum(move_times) / repeats
	diff_time = avg_move_time - calc_time
	print 'speed %.2f degrees/sec time_diff is\t %8.3f sec.' % (speed, diff_time)

def loop(tem_obj, center_time, step_time, half_loop_number):
	'''
	Equally spaced time loop centered around a value.
	'''
	loop_number = half_loop_number*2 + 1
	for i in range(loop_number):
		target_time = (i-half_loop_number)*step_time + center_time
		speed = float(delta_angle) / target_time
		if target_time >=180 or target_time < 1:
			print 'invalid target time: %.2f seconds, ignored' %(target_time)
			continue
		testTiltSpeed(tem_obj, delta_angle, speed)

if __name__ == '__main__':
	print "Edit file to set instrument"
	# Check from 40 s to 140 s target time
	loop(c, 90, 10, 5)
