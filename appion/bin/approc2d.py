#!/usr/bin/env python

from appionlib import proc2dLib

if __name__ == '__main__':
	approc2d = proc2dLib.ApProc2d(quiet=True)
	approc2d.start()
	approc2d.close()
