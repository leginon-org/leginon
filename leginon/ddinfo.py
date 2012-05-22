import os
from leginon import leginondata
import sys

def parseInfoTxt(infopath):
	if not os.path.isfile(infopath):
		return False
	infile = open(infopath,'r')
	lines = infile.readlines()
	params = {}
	for line in lines:
		bits = line[:-2].split('=')
		params[bits[0]]='='.join(bits[1:])
	return params

def commitToDatabase(imagedata,params):
	for key in params.keys():
		qkey = leginondata.DDinfoKeyData(name=key)
		qvalue = leginondata.DDinfoValueData(infokey=qkey,infovalue=params[key])
		if imagedata.__class__ == leginondata.AcquisitionImageData:
			qvalue['image']=imagedata
		elif imagedata.__class__ == leginondata.BrightImageData:
			qvalue['bright']=imagedata
		elif imagedata.__class__ == leginondata.DarkImageData:
			qvalue['dark']=imagedata
		elif imagedata.__class__ == leginondata.NormImageData:
			qvalue['norm']=imagedata
		else:
			print 'image data class unknown',imagedata
			sys.exit(1)
		qvalue.insert()

def saveImageDDinfoToDatabase(imagedata,infopath):
	params = parseInfoTxt(infopath)
	if params:
		commitToDatabase(imagedata,params)

def saveSessionDDinfoToDatabase(sessiondata):
	qcam = leginondata.CameraEMData(session=sessiondata)
	qcam['save frames'] = True
	acqimages = leginondata.AcquisitionImageData(camera=qcam).query()
	for imagedata in acqimages:
		infopath = os.path.join(sessiondata['image path'],imagedata['filename']+'.frames','info.path')
		saveImageDDinfoToDatabase(imagedata,infopath)

if __name__ == '__main__':
	infopath = sys.argv[1]
	imagename = sys.argv[2]
	imagename = imagename.split('.mrc')[0]
	imagedata = leginondata.AcquisitionImageData(filename=imagename).query(results=1)[0]
	saveImageDDinfoToDatabase(imagedata,infopath)
