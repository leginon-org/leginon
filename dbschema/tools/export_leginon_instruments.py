#!/usr/bin/env python
import sys
import copy
from leginon import leginondata
from pyami import jsonfun
'''
	This program export a json file required to insert instrument,
	client list, and magnifications into another leginon database,
	typically on a different host.
	Usage: export_leginon_instruments.py source_database_hostname
'''

class InstrumentJsonMaker(jsonfun.DataJsonMaker):
	def __init__(self,params, interactive=False):
		super(InstrumentJsonMaker,self).__init__(leginondata)
		self.hostnames = []
		self.interactive = interactive
		try:
			self.validateInput(params)
		except ValueError as e:
			print("Error: %s" % e)
			self.close(1)

	def validateInput(self, params):
		if len(params) < 2:
			print("Usage export_leginon_instruments.py source_database_hostname <hostname1,hostname2>")
			print("(hostname1, hostname2 etc are specific instrument hostname to export. default will export all)")
			self.close(1)
		database_hostname = leginondata.sinedon.getConfig('leginondata')['host']
		if params[1] != database_hostname:
			raise ValueError('leginondata in sinedon.cfg not set to %s' % params[1])
		if len(params) > 2 and params[2]:
			self.hostnames = params[2].split(',')

		if len(params) > 3:
			include_sim = params[3] # boolean
		else:
			include_sim = False
		self.exclude_sim = not include_sim
		self.instruments = self.getSourceInstrumentData(exclude_sim=not include_sim)

	def getSourceInstrumentData(self, exclude_sim=False):
		kwargs = {}
		q = leginondata.InstrumentData()
		results = q.query()
		real_instruments = []
		for r in results:
			if r['hidden']:
				continue
			if (not exclude_sim or not r['name'].startswith('Sim')) and not r['hostname'] in ('fake','appion'):
				if not self.hostnames or r['hostname'] in self.hostnames:
					# specific name if have specification
					real_instruments.append(r)
		if not real_instruments:
			print("ERROR: ....")
			raise ValueError("  No real instrument found")
			sys.exit()
		real_instruments.reverse()
		return real_instruments

	def getClients(self, interactive=False):
		# simulated instrument is never a leginon client
		real_instruments = self.getSourceInstrumentData(exclude_sim=self.exclude_sim)
		clients = []
		possible_clients = list(map((lambda x: x['hostname']), real_instruments))
		possible_clients = list(set(possible_clients))
		possible_clients.sort()
		print('Here are the possible client names.')
		for c in possible_clients:
			print(('\t'+c))
		if self.interactive:
			return interactiveDeleteClients(possible_clients)
		print('You can modify the resulting instrument_clients.json to clean this up.')
		return possible_clients

	def interactiveDeleteClients(self, possible_clients):
		answer = input('Do you want to remove some of them ? (Y/y or N/n)')
		if answer.lower() in 'y':
			for c in possible_clients:
				answer = input('Is this a good host %s ? (Y/y or N/n)' % (c,))
				if answer.lower() in 'y':
					clients.append(c)
		else:
			clients = copy.copy(possible_clients)		
		return clients

	def publishInstruments(self):
		print('Adding Instruments')
		self.publish(self.instruments)

	def publishMagnifications(self, tem):
		results = leginondata.MagnificationsData(instrument=tem).query(results=1)
		if results:
			print('Adding Magnifications')
		self.publish(results)
	
	def publishClients(self, clients):
		#CameraSensitivity
		results = leginondata.ConnectToClientsData().query(results=1)
		if results:
			print('Adding Clients')
		else:
			print('No client connection entry found')
			self.close(1)
		q = leginondata.ConnectToClientsData(initializer=results[0])
		q['clients'] = clients
		self.publish([q,])

	def run(self):
		self.publishInstruments()
		json_filename = 'instruments.json'
		self.writeJsonFile(json_filename)
		self.alldata = []
		for instr in self.instruments:
			if instr['cs'] is not None:
				# Magnifications for tem
				self.publishMagnifications(instr)
				json_filename = 'mags_%s+%s.json' % (instr['hostname'],instr['name'])
				self.writeJsonFile(json_filename)
			self.alldata = []
		clients = self.getClients()
		self.publishClients(clients)
		json_filename = 'instrument_clients.json'
		self.writeJsonFile(json_filename)

	def close(self, status=0):
		if status:
			print("Exit with Error")
			sys.exit(1)
		if self.interactive:
			input('hit enter when ready to quit')

if __name__=='__main__':
	app = InstrumentJsonMaker(sys.argv, interactive=False)
	app.run()
	app.close()
	 
