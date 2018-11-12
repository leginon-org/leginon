#!/usr/bin/env python
import os
import time

from appionlib.uploadSEMImages import UploadSEMImages
cmd = os.popen("csh -c 'modulecmd python load imod'")
exec(cmd)

#=====================
if __name__ == '__main__':
	upimages = UploadSEMImages()
	upimages.start()
	upimages.close()
