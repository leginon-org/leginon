#!/usr/bin/env python
import sys
import schemabase
import leginon.leginondata

class SchemaUpdate15653(schemabase.SchemaUpdate):
	'''
  This will enter in leginondb the Cs value for all tems that
	have been used for saved images.
	Because Cs can be different by TEM, this script is interactive. 
	'''
	def validateCsValue(self,answer,default_cs_mm):
		while True:
			if not answer:
				answer = default_cs_mm
				break
			try:
				answer = float(answer)
				if answer > 0.1 and answer < 5:
					break
				else:
					print "Cs value must be a reasonable number in mm, try again"
			except ValueError:
				print "Cs value must be a number in mm, try again"
			answer = raw_input('(default=%.3f): ' % cs_mm)
		return answer
 
	def upgradeLeginonDB(self):
		print "\n This schema upgrade requires knowledge of microscopy."
		print "If you don't know what Spherical Aberration Constant is,"
		print "you should get help."
		answer = raw_input('Are you ready?(Y/N):')
		if not answer.lower().startswith('y'):
			sys.exit()
		# create column if not exist
		if not self.leginon_dbupgrade.columnExists('InstrumentData', 'cs'):
				self.leginon_dbupgrade.addColumn('InstrumentData', 'cs',self.leginon_dbupgrade.float)
		query = 'SELECT `REF|InstrumentData|tem` as tem from ScopeEMData WHERE 1 group by `REF|InstrumentData|tem`;'
		results = self.leginon_dbupgrade.returnCustomSQL(query)
		for r in results:
			# old database might have none as tem reference
			if r[0] is None:
				continue
			temid = int(r[0])
			temq = leginon.leginondata.InstrumentData()
			temdata = temq.direct_query(temid)
			# old database might have none deleted tem
			if temdata is None:
				continue
			if temdata['cs'] is not None:
				cs_mm = temdata['cs'] * 1e3
				print "\n TEM %s on host %s has Cs value of %.3f mm. Enter a new value if you'd like to change it.  Otherwise, hit return" % (temdata['name'],temdata['hostname'],cs_mm)
			else:
				cs_mm = 2.0
				print "\n TEM %s on host %s has no Cs value. Enter a value if you know it. hit return will default it to 2.0 mm" % (temdata['name'],temdata['hostname'])
			answer = raw_input('(default=%.3f): ' % cs_mm)
			new_cs_mm = self.validateCsValue(answer,cs_mm)
			self.leginon_dbupgrade.updateColumn('InstrumentData','cs',new_cs_mm*1e-3,'`DEF_id`=%d' % temid, timestamp=False)

if __name__ == "__main__":
	update = SchemaUpdate15653()
	update.setRequiredUpgrade('leginon')
	update.run()

