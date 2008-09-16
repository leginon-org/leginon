
## python
import time
import os
## appion
import apDisplay

"""
A large collection of SPIDER functions

I try to keep the trend
image file: 
	*****img.spi
doc/keep/reject file: 
	*****doc.spi
file with some data:
	*****data.spi

that way its easy to tell what type of file it is

neil
"""

#===============================
def spiderOutputLine(int1, int2, float1, float2, float3, float4, float5, float6=1.0):
	line = "%04d" % int1
	line += " %1d" % int2
	line += apDisplay.leftPadString("%4.6f" % float1, n=12)
	line += apDisplay.leftPadString("%4.6f" % float2, n=12)
	line += apDisplay.leftPadString("%4.6f" % float3, n=12)
	line += apDisplay.leftPadString("%4.6f" % float4, n=12)
	line += apDisplay.leftPadString("%4.6f" % float5, n=12)
	line += apDisplay.leftPadString("%4.6f" % float6, n=12)
	line += "\n"
	return line


#===============================
def spiderOutputLine3(int1, float1, float2, float3):
	line = "%04d" % int1
	line += " %1d" % 3
	line += apDisplay.leftPadString("%4.6f" % float1, n=12)
	line += apDisplay.leftPadString("%4.6f" % float2, n=12)
	line += apDisplay.leftPadString("%4.6f" % float3, n=12)
	line += "\n"
	return line

