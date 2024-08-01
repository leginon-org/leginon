#!/usr/bin/env python
import os, shutil

from leginon import leginondata
from sinedon import directq

session_name = input('Session name= ')
image_name = input('Give image name of one of the image in the series = ')
keep_one_answer = input('Keep this image and delete the rest ? (Y/N/y/n) ')
keep_one = keep_one_answer.lower() == 'y'

if image_name.endswith('.mrc'):
	image_name = image_name[:-4]

def getSessionData(session_name):
	try:
		return leginondata.SessionData(name=session_name).query(results=1)[0]
	except IndexError:
		raise ValueError('%s not found as a session' % session_name)

def getImageData(session, filename):
	results = leginondata.AcquisitionImageData(session=session, filename=filename).query(results=1)
	if not results:
		raise ValueError('Can not find %s in session %s' % (filename+'.mrc',session['name']))
	return results[0]

def getSeriesName(image_name):
	bits = image_name.split('_')
	series_name = '_'.join(bits[1:-2])
	if not series_name:
		raise ValueError('Invalid series name %s' % (series_name))
	return series_name

def setupSeries(exemplar_image, keep_one=False):
	'''
	Find AcquisitionImageData from the same target as exemplar and validate series
	'''
	if not exemplar_image['target']:
		raise ValueError('image is not from a target')
	namelist = []
	images = leginondata.AcquisitionImageData(target=exemplar_image['target']).query()
	namelist = list(map((lambda x: x['filename']+'.mrc'), images))
	if keep_one:
		try:
			namelist.remove(exemplar_image['filename']+'.mrc')
			print(('Leave out %s.mrc' % (exemplar_image['filename'])))
		except ValueError:
			print('Error: Exemplar image not in the list.  This should never happen')
			raise RuntimeError('Aborted')
	answer = input('There are %d images to delete.  Are you sure ? (Y/y/N/n)' % (len(namelist)))
	if answer.lower() != 'y':
		raise RuntimeError('Aborted')
	series_name = getSeriesName(exemplar_image['filename'])
	diffraction_path = os.path.join(exemplar_image['session']['image path'].replace('rawdata','diffraction'),series_name)
	if not os.path.isdir(diffraction_path):
		raise RuntimeError('smv files folder %s not exists' % diffraction_path)
	bin_path = os.path.join(exemplar_image['session']['image path'].replace('rawdata','diffraction_raw'),series_name)
	if not os.path.isdir(bin_path):
		raise RuntimeError('raw bin files folder %s not exists' % bin_path)
	return namelist

def recordDeletedDiffractionSeries(emtarget, comment):
	# data without DiffractionSeriesData would not have been uploaded
	r = leginondata.DiffractionSeriesData(emtarget=emtarget).query(results=1)
	if r:
		session = emtarget['session']
		q = leginondata.DeletedDiffractionSeriesData(session=session,
series=r[0], comment=comment)
		q.insert()
	else:
		raise ValueError('Can not find diffraction series to record deletion')

def deleteSeriesInDB(exemplar_image, keep_one=False):
	'''
	Delete AcquisitionImageData from the same target as exemplar in leginon database.
	'''
	comment = 'all'
	lconfig = directq.sinedon.getConfig('leginondata')
	q = "Delete from %s.`AcquisitionImageData` where `REF|AcquisitionImageTargetData|target`=%d" % (lconfig['db'],exemplar_image['target'].dbid)
	if keep_one:
		q += " and `DEF_id` != %d" % exemplar_image.dbid
		comment = 'keep %d' %  exemplar_image.dbid
	print(q)
	directq.complexMysqlQuery('leginondata', q)
	# record the deletion in database according to keep_one value
	recordDeletedDiffractionSeries(exemplar_image['emtarget'], comment)

def removeDiffrFiles(session, series_name):
	diffraction_path = os.path.join(session['image path'].replace('rawdata','diffraction'),series_name)
	bin_path = os.path.join(session['image path'].replace('rawdata','diffraction_raw'),series_name)
	print(('Removing tree of %s' % diffraction_path))
	shutil.rmtree(diffraction_path)
	print(('Removing tree of %s' % bin_path))
	shutil.rmtree(bin_path)

def removeMrcFiles(session, namelist):
	for mrcfile in namelist:
		mrc_path = os.path.join(session['image path'], mrcfile)
		print(('Removing file of %s' % mrc_path))
		os.remove(mrc_path)

# Main process 
session = getSessionData(session_name)
image = getImageData(session, image_name)
answer = input('Are you ready delete images from the same target as %s ? (Y/y/N/n)' % (image['filename']+'.mrc'))
if answer.lower() == 'y':
	series_name = getSeriesName(image['filename'])
	mrclist = setupSeries(image, keep_one)
	deleteSeriesInDB(image, keep_one)
	removeMrcFiles(session, mrclist)
	removeDiffrFiles(session, series_name)
else:
	print('Aborted')
