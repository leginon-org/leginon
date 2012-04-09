#!/usr/bin/env python
from appionlib import apTomoFullRecon

if __name__ == '__main__':
	app = apTomoFullRecon.ETomoMaker()
	app.start()
	app.close()
