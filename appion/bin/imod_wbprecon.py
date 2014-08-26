#!/usr/bin/env python
from appionlib import apTomoFullRecon

if __name__ == '__main__':
	app = apTomoFullRecon.ImodFullMaker()
	app.start()
	app.close()
