#! /usr/bin/env python
# lists available GPUs, up to MAX, one on each line
# available is defined as 
#	maxLoad=0.5
#	maxMemory = 0.5

MAX=12
import GPUtil
#GPUtil.showUtilization(all=True)
deviceIDs = GPUtil.getAvailable(limit=MAX)
#print "Available GPUs:"
for ID in deviceIDs:
	print(ID)

