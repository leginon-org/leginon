# standard lib
import os

# myami
import leginon.leginondata
import sinedon

# local
import read

# other
import MySQLdb

def look_up(filename):
	legname = os.path.basename(filename)
	if legname.endswith('.mrc'):
		legname = legname[:-4]

	# find possible sessions that contain this image
	session_str = legname.split('_')[0]
	q = 'SELECT name from SessionData WHERE name LIKE "%s%%"' % (session_str,)
	conf = sinedon.getConfig('leginondata')
	db = MySQLdb.connect(**conf)
	cur = db.cursor()
	cur.execute(q)
	sessions = cur.fetchall()
	session_names = [session[0] for session in sessions]
	# first look for AcquisitionImageData
	for session_name in session_names:
		sessiondata = leginon.leginondata.SessionData(name=session_name)
		sessiondata = sessiondata.query(results=1)[0]
		imdata = leginon.leginondata.AcquisitionImageData(session=sessiondata, filename=legname)
		imdata = imdata.query()
		if imdata:
			fullpath = os.path.join(sessiondata['image path'], legname+'.mrc')
			return fullpath
	# then look for reference images
	for imclass in (leginon.leginondata.DarkImageData, leginon.leginondata.NormImageData, leginon.leginondata.BrightImageData):
		imdata = imclass(filename=legname)
		imdata = imdata.query()
		if imdata:
			sessiondata = imdata[0]['session']
			fullpath = os.path.join(sessiondata['image path'], legname+'.mrc')
			return fullpath

	raise ValueError('no image found in db: %s' % (filename,))

class Leginon(read.Read):
	'''
	Subclass of Read that will take care of looking up the absolute path
	of an image in the Leginon db when given only the base name.
	'''
	required_args = {'filename': look_up}

	def make_dirname(self):
		## disable caching for frame requests
		if 'frame' in self.kwargs:
			self.disable_cache = True
			self._dirname = None
		else:
			self.disable_cache = False
			self._dirname = os.path.join('Leginon',os.path.basename(self.kwargs['filename']))

