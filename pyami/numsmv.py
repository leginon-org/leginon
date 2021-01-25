#!/usr/bin/env python
import sys
import numpy
import datetime

# attempt to use weakattr
try:
	from pyami import weakattr
except:
	pass

'''
Write smv format image files given the numpy array.
smv format is described in
https://strucbio.biologie.uni-konstanz.de/ccp4wiki/index.php/SMV_file_format

This only modify the size1 and size2 from the standard header.
'''

# header (name, type, default, format
HEADER_FIELDS = (
	# required for reading data
	('HEADER_BYTES', int, 512, '{:>5}'),
	('TYPE', str, 'unsigned_short', '{0}'),
	('BYTE_ORDER', str, 'little_endian', '{0}'),
	('DIM', int, 2, '{:1}'),
	('SIZE1', int, 2048, '{:>5}'),
	('SIZE2', int, 2048, '{:>5}'),
	# imaging geometry
	('DISTANCE', float, 1000.0, '{:7.1f}'), #mm
	('WAVELENGTH', float, 0.025014041, '{:12.8f}'), # angstrom
	('PIXEL_SIZE', float, 0.028, '{:8.3f}'), # mm
	('OSC_RANGE', float, 1.000, '{:8.3f}'), #degrees. Can this be negative ?
	('OSC_START', float, 0.000, '{:8.3f}'), #degrees
	('BEAM_CENTER_X', float, 0.000, '{:8.3f}'), # mm
	('BEAM_CENTER_Y', float, 0.000, '{:8.3f}'), # mm
	('PHI', float, 0.000, '{:8.3f}'), #spindle angle in degrees same as OSC_START ?
	('TWOTHETA', float, 0.0, '{:8.3f}'), # detector angle to beam normal plane in degrees
	# timing
	('TIME', float, 1.0, '{0}'), # seconds
	('ACC_TIME', int, 1000, '{0}'), # milliseconds
	# detector identity
	# DIALS wants GAIN not be 1 to signal that this is an integration camera
	# and automatically set background.model=simple
	('GAIN', float, 1.00, '{:8.2f}'),
	# assume detector is native at BIN 2x2 because Dials does not read BIN.
	('BIN', tuple, (1,1), '{0[0]:1}x{0[1]:1}'),
	('ADC', str, 'fast', '{0}'),
	# ADSC info
	('BIN_TYPE', str, 'HW', '{0}'),
	('CREV', int, 1, '{:>3}'),
	#('DETECTOR_SN', int, 1, '{0}'),
	# setup info
	('BEAMLINE', str, 'nan', '{0}'),
	# pthers
	('DATE', datetime.datetime, datetime.datetime.today(), '{0}'), #UNIX date in current timezone
	('IMAGE_PEDESTAL', float, 0.0, '{:7.1f}'), # DIALS can take this. median of min values from all frames.
	# my own keys for my record
	('LEGINON_OFFSET', float, 0.0, '{:7.1f}'),#offset added when converting float32 mrc file to smv
)

DEPRECATED_KEYS = ['DETECTOR_SN',]
# (header_value, numpy_dtype, number_of_bytes)
TYPE_MAP = [('unsigned_short', numpy.uint16, 2),]

VALID_KEYS = map((lambda x: x[0]),HEADER_FIELDS)

def newHeader(header_fields=HEADER_FIELDS):
	'''
Return a new initialized header dictionary.
All fields are initialized to default.
	'''
	headerdict = {}
	for field in header_fields:
		name = field[0]
		default = field[2]
		headerdict[name] = default
	return headerdict

def formatHeader(headerdict, set_default=False):
	'''
	Convert header dictionary which values are in the python type to a string.
	Join the key and values to the required format.  The result is not yet
	padded to header_bytes.
	'''
	names = map((lambda x: x[0]), HEADER_FIELDS)
	header = ''
	for i, name in enumerate(names):
		try:
			value = headerdict[name]
		except KeyError:
			if not set_default:
				# ignore missing key
				continue
			else:
				value = HEADER_FIELDS[i][2]
		f_value = HEADER_FIELDS[i][3]
		v_type = HEADER_FIELDS[i][1]
		if v_type != str and type(value) == type('nan'):
			# default nan is a string regardless of type.
			str_value = value
		elif name == 'BIN':
			str_value = '%dx%d' % (value[0],value[1])
		elif name == 'DATE':
			str_value = value.strftime('%a %b %d %H:%M:%S %Y')
		else:
			str_value = f_value.format(value)
		h_item = '%s=%s;\n' % (name, str_value)
		header += h_item
	header = '{\n' + header + '}\n'
	filled_length = len(header)
	header_bytes = headerdict['HEADER_BYTES']
	spaces = ' '*(header_bytes-filled_length-1)
	header += spaces + '\n'
	return header

def validate_and_convert(key, value):
	try:
		i = VALID_KEYS.index(key)
	except:
		raise ValueError('Key not valid: %s' % (key,))
	valid_type = HEADER_FIELDS[i][1]
	# Handle nan
	if value == 'nan':
		return value
	if key == 'DETECTOR_SN' and value == 'unknown':
		return 1
	# Parsing Bin
	if key == 'BIN':
		if isinstance(value, tuple):
			bits = value
		else:
			bits = value.split('x')
		if len(bits) != 2:
			raise ValueError('BIN not in format like 1x1 but %s' % (value,))
		try:
			int(bits[0]) > 0
			int(bits[1]) > 0
		except:
			raise ValueError('BIN not in format like 1x1 but %s' % (value,))
		# Not sure this is XxY or YxX
		return (int(bits[0]),int(bits[1]))
	if key == 'DATE':
		try:
			return datetime.datetime.strptime(value, '%a %b %d %H:%M:%S %Y')
		except:
			print('Warning: Date not valid, use current date time')
			return datetime.datetime.today()
	# All other keys
	try:
	  return valid_type(value)
	except:
		raise

def parseHeader(headerbytes):
	'''
	Parse the 512 byte SMV header into a header dictionary.
	'''
	curly_bracket_bits = headerbytes[1:].split('}')
	bits = curly_bracket_bits[0].split(';')
	headerdict = {}
	for h in bits:
		lines = h.split('\n')
		for l in lines:
			if '=' in l:
				try:
					key, value_str = l.split('=')
					value = validate_and_convert(key, value_str)
					headerdict[key] = value
				except Exception as e:
					if key in DEPRECATED_KEYS:
						continue
					print('Invalid parsing: "%s" with error-\n  %s' % (l,e))
					sys.exit(1)
	return headerdict

def readHeaderFromFileObj(fobj):
	fobj.seek(0)
	headerbytes = fobj.read(512)  # read default size
	headerdict = parseHeader(headerbytes)
	if headerdict['HEADER_BYTES'] != 512:
		# redo parse header
		fobj.seek(0)
		headerbytes = fobj.read(headerdict['HEADER_BYTES'])
		headerdict = parseHeader(headerbytes)
	return headerdict

def updateHeader(headerdict, key, value):
	'''
	Update an item in header dict with validation
	'''
	try:
		value = validate_and_convert(key, value)
	except Exception as e:
		print('Updating %s failed with value %s' % (key, value,))
	headerdict[key] = value
	return headerdict

#-----END of Header functions
#-----START of Data functions
def getDataBytesPerPixel(header_type_string):
	print header_type_string
	types = map((lambda x: x[0]),TYPE_MAP)
	i = types.index(header_type_string)
	return TYPE_MAP[i][2]

def getDataNumpyType(header_type_string):
	types = map((lambda x: x[0]),TYPE_MAP)
	i = types.index(header_type_string)
	return TYPE_MAP[i][1]

def readDataFromFileObj(fobj, headerdict):
	'''
	Read data portion of SMV file from the file object fobj.
	Both mrcmode and shape have been determined from the MRC header.
	Returns a new numpy ndarray object.
	'''
	bytes_per_pixel = getDataBytesPerPixel(headerdict['TYPE'])
	numpy_type = getDataNumpyType(headerdict['TYPE'])
	header_bytes = headerdict['HEADER_BYTES']
	start = header_bytes  # right after header
	shape = (headerdict['SIZE1'],headerdict['SIZE2'])
	datalen = numpy.prod(shape)
	fobj.seek(start)
	a = numpy.fromfile(fobj, dtype=numpy_type, count=datalen)
	a.shape = shape
	return a

def setHeader(a, headerdict):
	'''
Attach an header to the array.
	'''
	try:
		weakattr.set(a, 'smvheader', headerdict)
	except:
		pass

# Functions to be called from outside.
def read(filename):
	'''
	Read header and data of the filename. The header is saved in smvheader attribute
	of the resulting numpy array if pyami is in the python path.
	'''
	fobj = open(filename, 'rb')
	headerdict = readHeaderFromFileObj(fobj)
	a = readDataFromFileObj(fobj, headerdict)
	fobj.close()

	## store keep header with image
	setHeader(a, headerdict)
	return a

def write(a, imfile=None, offset=0, header_updates={}):
	'''
	Convert array to unsigned 16 bit gray scale and save to filename.
	'''
	if offset:
		a = a+numpy.ones(a.shape)*offset
	if a.min() < 0:
		print '%s min of %d was truncated to 0' % (imfile, a.min())
		a[a < 0] = 0
	if a.max() >= 2**16:
		print '%s max of %d was truncated to %d' % (imfile, a.max(), 2**16-1)
		a[a >= 2**16] = 2**16-1
	# known smv format are all square.
	shape = a.shape
	shape_max = max(shape)
	shape_min = min(shape)
	if shape_min != shape_max:
		print("Warning: truncate to square shape")
		crop_start = (shape_max-shape_min)/2
		if shape[0] == max(shape):
			a = a[crop_start:crop_start+shape_min,:]
		else:
			a = a[:,crop_start:crop_start+shape_min]
	# known smv files are all uint16
	a = a.astype(numpy.uint16)
	headerdict = newHeader()
	header_updates['SIZE1']=a.shape[0]
	header_updates['SIZE2']=a.shape[1]
	header_updates['LEGINON_OFFSET']=offset
	for k in header_updates.keys():
		v = header_updates[k]
		headerdict = updateHeader(headerdict,k,v)
	# new header has complete default values
	headbytes = formatHeader(headerdict)
	outf = open(imfile,'wb')
	outf.write(headbytes)
	outf.write(a)
	outf.close()

def readHeaderFromFile(filename):
	fobj = open(filename)
	h = readHeaderFromFileObj(fobj)
	fobj.close()
	return h

def update_file_header(filename, headerdict, set_default=False):
	'''
	open the SMV file header, update the fields given by headerdict.
	'''
	# Check input
	for k in headerdict.keys():
		try:
			v = headerdict[k]
			v = validate_and_convert(k,headerdict[k])
			headerdict[k] = v
		except Exception as e:
			raise ValueError('Updating %s failed with value %s' % (k, v,))
	# Open header and update
	f = open(filename, 'rb+')
	oldheader = readHeaderFromFileObj(f)
	oldheader.update(headerdict)
	headerbytes = formatHeader(oldheader, set_default)
	f.seek(0)
	f.write(headerbytes)
	f.close()

def validate_file_length(filename):
	h = readHeaderFromFile(filename)
	fsize = os.path.getsize(filename)
	return fsize == h['HEADER_BYTES']+headerdict['SIZE1']*headerdict['SIZE2']*getDataBytesPerPixel(headerdict['TYPE'])

if __name__ == '__main__':
	shape = (1000,1000)
	inset_shape = (200,200)
	a = numpy.zeros(shape)
	a[0:inset_shape[0],0:inset_shape[1]] = numpy.ones(inset_shape)
	write(a, 'test.smv')
	print('Written test.smv')
