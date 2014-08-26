#!/usr/bin/env python
from appionlib import apTomoSubRecon

if __name__ == '__main__':
	app = apTomoSubRecon.SubTomoETomoMaker()
	app.start()
	app.close()
