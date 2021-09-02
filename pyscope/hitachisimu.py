#!/usr/bin/env python
import socket
import time

eof_marker = "\r"

class HitachiSimu(object):
	def __init__(self):
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind(('127.0.0.1', 12068))
		self.server.listen(5)
		self.return_codes = {8000:'OK.'}

		self.onInit()

	def setDataTypes(self):
		self.data_types = {
			"Beam": [int,],
			"Coil BH": ['hexdec','hexdec'],
			"Coil BT": ['hexdec','hexdec'],
			"Coil ISF": ['hexdec','hexdec'],
			"Coil IA": ['hexdec','hexdec'],
			"Coil PA": ['hexdec','hexdec'],
			"Coil CS": ['hexdec','hexdec'],
			"Coil OS": ['hexdec','hexdec'],
			"Coil IS": ['hexdec','hexdec'],
			"Column": [str,],
			"Column Magnification": [int,],
			"Column Mode": ['hexdec','hexdec'],
			"COND_APT Position": [int,int],
			"EmissionCurrent": [float,],
			"EvacValve": [int,],
			"EvacGauge": [float,],
			"HighVoltage": [float,],
			"Lens C1": ['hexdec',],
			"Lens C2": ['hexdec',],
			"Lens C3": ['hexdec',],
			"Lens OBJ": ['hexdec',],
			"OBJ_APT Position": [int,],
			"SA_APT Position": [int,],
			"Screen Position": [int,],
			"SpotMask Position": [int,],
			"Stage SpecimenNo": [int,],
			"StageXY": [int, int],
			"StageZ": [int,],
			"StageTilt": [float,],
			"StageTilt Speed": [int,],
			"StageAzim": [float,],
		}

	def setDataValues(self):
		half = int('3FFC00',16)/2
		self.data_values = {
			"Beam": [int,],
			"Coil BH": [hex(half),hex(half)],
			"Coil BT": [hex(half),hex(half)],
			"Coil ISF": [hex(half),hex(half)],
			"Coil IA": [hex(half),hex(half)],
			"Coil PA": [hex(half),hex(half)],
			"Coil CS": [hex(half),hex(half)],
			"Coil OS": [hex(half),hex(half)],
			"Coil IS": [hex(half),hex(half)],
			"Column": ['BrightnessFree',],
			"Column Magnification": [120000,],
			"Column Mode": [hex(15),hex(2)], #???
			"COND_APT Position": [0,0],
			"EmissionCurrent": [0.1,],
			"EvacGauge": [0.1,],
			"EvacValve": [0,],
			"HighVoltage": [100.0,],
			"Lens C1": [hex(0),],
			"Lens C2": [hex(0),],
			"Lens C3": [hex(0),],
			"Lens OBJ": [hex(0),],
			"OBJ_APT Position": [0,],
			"SA_APT Position": [0,],
			"Screen Position": [0,],
			"SpotMask Position": [0,],
			"Stage SpecimenNo": [1,],
			"StageXY": [0,0],
			"StageZ": [0,],
			"StageTilt": [0.0,],
			"StageTilt Speed": [100,],
			"StageAzim": [0.0,],
		}

	def onInit(self):
		self.setDataTypes()
		self.setDataValues()
		conn, address = self.server.accept()
		print 'server 127.0.0.1:12068 is ready'
		text = ''
		try:
			while True:
				d = conn.recv(1) 
				if d == eof_marker:
					print text
					respond = self.makeResponse(text)
					conn.send(respond)
					text = ''
					time.sleep(0.02)
				else:
					text += d
		except KeyboardInterrupt:
			conn.close()
		except Exception, e:
			print e
			conn.close()

	def makeResponse(self, text):
		if text.startswith('Get'):
			response_text = self._getData(text[4:])
		if text.startswith('Set'):
			response_text = self._setData(text[4:])
		if response_text:
			return response_text+eof_marker
		return ''

	def _getData(self, subtext):
		bits = subtext.split(' ')
		sub_code = bits[0]
		cmd = sub_code
		if len(bits) > 1:
			expansion_code = bits[1]
			cmd += ' '+expansion_code
		if cmd in self.data_types.keys():
			key = cmd
		else:
			key = sub_code
		data_bits = []
		for i, d_type in enumerate(self.data_types[key]):
			if d_type == int:
				data_bits.append('%d' % self.data_values[key][i])
			elif d_type == float:
				data_bits.append('%.1f' % self.data_values[key][i])
			elif d_type == 'hexdec' or d_type == str:
				data_bits.append(self.data_values[key][i])
		data = ','.join(data_bits)
		return 'Get '+subtext+' '+data

	def _setData(self, subtext):
		bits = subtext.split(' ')
		sub_code = bits[0]
		cmd = sub_code
		if len(bits) > 2:
			expansion_code = bits[1]
			cmd += ' '+expansion_code
		if cmd in self.data_types.keys():
			key = cmd
		else:
			key = sub_code
		data_code = bits[-1]
		data_bits = data_code.split(',')
		if sub_code in ('Lens','Coil'):
			# remove 'FF'
			data_bits = data_bits[1:]
		for i, d_type in enumerate(self.data_types[key]):
			if d_type == int:
				self.data_values[key][i] = int(data_bits[i])
			elif d_type == float:
				self.data_values[key][i] = float(data_bits[i])
			elif d_type == 'hexdec' or d_type == str:
				if sub_code == 'Column' and expansion_code == 'Mode' and int(data_bits[i],16) == int('FF',16):
					# Don't change if FF
					continue
				self.data_values[key][i] = data_bits[i]
		data = ','.join(data_bits)
		print data
		if sub_code == 'Stage' and expansion_code == 'SpecimenNo':
			return ''
		return 'Set '+cmd+' 8000,"OK."'

if __name__== "__main__":
	app = HitachiSimu()

