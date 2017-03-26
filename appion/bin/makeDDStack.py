#!/usr/bin/env python

from appionlib import apDDStackMaker
'''
Basic DDStack maker.  This uses the base class
with no alignment capacity.  For testing mainly
'''
if __name__ == '__main__':
	makeStack = apDDStackMaker.FrameStackLoop()
	makeStack.run()
