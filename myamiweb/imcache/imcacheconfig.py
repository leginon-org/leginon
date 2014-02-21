# config file for imcached

# camera name pattern to cache.  For example 'GatanK2' will restrict it
# only to camera name containing the string
camera_name_pattern = ''

# time in seconds to wait between consecutive queries
query_interval = 5

# limit query to later than this timestamp (mysql style: yyyymmddhhmmss)
min_timestamp = '20130126000000'

# limit query to start at this image id
start_id = 0

# root dir of cache.  session subdirs will be added automatically
cache_path = '/srv/cache/dbem'

# maximum image dimension after conversion
redux_maxsize1 = 4096
redux_maxsize2 = 1024

# initial redux read and resize before calculating power and final
redux_args1 = {
	'pipes': 'read:Read,shape:Shape',
	'cache': False,
}

# redux to create final image for cache
redux_args_jpg = {
	'cache': False,
	'pipes': 'shape:Shape,scale:Scale,format:Format',
	'scaletype': 'stdev',
	'scalemin': -5,
	'scalemax': 5,
	'oformat': 'JPEG',
}

# redux to create final power image for cache
redux_args_pow = {
	'cache': False,
	'pipes': 'power:Power,shape:Shape,mask:Mask,scale:Scale,format:Format',
	'power': True,
	'maskradius': 10,
	'scaletype': 'stdev',
	'scalemin': -5,
	'scalemax': 5,
	'oformat': 'JPEG',
}

