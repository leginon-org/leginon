# config file for imcached

# time in seconds to wait between consecutive queries
query_interval = 5

# limit query to later than this timestamp (mysql style: yyyymmddhhmmss)
min_timestamp = '20130114120000'

# limit query to start at this image id
start_id = 0

# root dir of cache.  session subdirs will be added automatically
cache_path = '/tmp/imcache'

# maximum image dimension after conversion
max_size = 1024

# redux args for image conversion
# filename and shape will be determined per image
redux_args = {
	'pipes': 'read:Read,shape:Shape,scale:Scale,format:Format',
	'cache': False,
	'oformat': 'JPEG',
	'scaletype': 'stdev',
	'scalemin': -5,
	'scalemax': 5,
}

