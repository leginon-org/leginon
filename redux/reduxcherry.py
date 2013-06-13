#!/usr/bin/env python

'''
hostname:8080/leginon/filename/512x512/5/image.jpg
'''

import cherrypy
import redux.pipeline

cherrypy.config.update({'server.socket_host': 'cronus2',
                        'server.socket_port': 8080,
                       })

class Pipe(object):
	def __init__(self, name):
		self.name = name

class ReduxRoot(object):
	'''
	def index(self):
		return 'hello'
	index.exposed = True
	'''
	def default(self, *args, **kwargs):
		cherrypy.response.headers['Content-Type'] = 'image/jpeg'
		pipes = args[:-1]
		outfilename = args[-1]
		pipes = [(pipe,pipe) for pipe in pipes]
		
		#return str(pipes) + '...' + str(kwargs)
		pl = redux.pipeline.Pipeline(pipes)
		return pl.process(**kwargs)
	default.exposed = True

def run():
	cherrypy.quickstart(ReduxRoot())

if __name__ == '__main__':
	run()
