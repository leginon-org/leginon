#!/usr/bin/env python

from mpi4py import MPI

TAG_AVAILABLE = 1
TAG_TASK = 2
TAG_DIE = 3

class TaskHandler(object):

	def __init__(self, *args, **kwargs):
		self.init_args = args
		self.init_kwargs = kwargs
		self.comm = MPI.COMM_WORLD
		self.rank = self.comm.Get_rank()

	def run_master(self):
		## make sure there are slaves to run the tasks
		if self.comm.Get_size() < 2:
			print 'need np > 1 to process'
			return

		## create a list of tasks
		try:
			tasks = self.initTasks(*self.init_args, **self.init_kwargs)
		except:
			self.kill_slaves()
			raise

		## distribute tasks to slaves
		for task in tasks:
			## wait for a slave to become available
			slave_rank = self.comm.recv(source=MPI.ANY_SOURCE, tag=TAG_AVAILABLE)
			## send task to slave
			self.comm.send(task, dest=slave_rank)

		## all tasks done, kill slaves
		self.kill_slaves()

	def kill_slaves(self):
		## kill slaves on their next request for task
		slave_ranks = range(1, self.comm.Get_size())
		while slave_ranks:
			slave_rank = self.comm.recv(source=MPI.ANY_SOURCE, tag=TAG_AVAILABLE)
			self.comm.send(None, dest=slave_rank, tag=TAG_DIE)
			slave_ranks.remove(slave_rank)
		print 'All slaves killed'

	def run_slave(self):
		## notify master of availability and wait for task
		self.comm.send(self.rank, dest=0, tag=TAG_AVAILABLE)
		task = self.comm.recv(source=0, tag=MPI.ANY_TAG)

		## Don't know how to check the tag, so using the message
		## itself to determine if this is a die instruction.
		## if message is None, then die.
		while task is not None:

			## The real work is done here:
			self.processTask(task)
			
			## notify master of availability and wait for task
			self.comm.send(self.rank, dest=0, tag=TAG_AVAILABLE)
			task = self.comm.recv(source=0, tag=MPI.ANY_TAG)
		print 'RANK %d done' % (self.rank,)

	def run(self):
		if self.rank == 0:
			self.run_master()
		else:
			self.run_slave()

