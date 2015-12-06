#!/usr/bin/env python
from appionlib import apImageUpload

if __name__ == '__main__':
	app = apImageUpload.ImageLoader()
	app.start()
	app.close()
