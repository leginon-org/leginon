#!/usr/bin/env python
from appionlib import apTomoSample

if __name__ == '__main__':
	app = apTomoSample.SampleMaker()
	app.start()
	app.close()
