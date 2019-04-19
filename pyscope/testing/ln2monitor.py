
TESTING = True
LOADER_TRIP_LEVEL = 5.0 # percentage
COLUMN_TRIP_LEVEL = 22.0 # percentage
RECOVER_TIME = 5*60 # expected recover time during fill

default_interval = 10*60 # 10 minutes
snooze_interval = 60*60 # snooze 60 minutes
silent_alarm = 2 # number of time to sound alarm before silent itself

if TESTING:
	default_interval = 5
	snooze_interval = 2
	RECOVER_TIME = 2 # expected recover time during fill

import time
import datetime
import threading
from pyscope import instrumenttype

import smtplib
from pyami import moduleconfig

def composeMessage(text):
	configs = moduleconfig.getConfigured('leginon.cfg')['Email']
	from email.MIMEMultipart import MIMEMultipart	
	from email.MIMEText import MIMEText
	msg=MIMEMultipart()
	msg['From']=configs['from']
	msg['To']=configs['to']
	msg['Subject']='N2 monitor Alarm'
	msg.attach(MIMEText(text,'plain'))
	return msg

def sendEmail(msg):
	if TESTING:
		sendFakeEmail(msg)
		return
	configs = moduleconfig.getConfigured('leginon.cfg')['Email']
	server = smtplib.SMTP(configs['host'],configs['port'])
	server.login(configs['user'],str(configs['password']))
	msg_obj = composeMessage(msg)
	text = msg_obj.as_string()
	server.sendmail(configs['from'],configs['to'], text)

def sendFakeEmail(msg):
	print msg

class N2Monitor(object):
	def __init__(self, logger):
		self.t = instrumenttype.getInstrumentTypeInstance('tem')
		self.logger = logger
		self.alarm_tripped = 0
		self.lock = True
		self.status = 'ok'

	def loop(self):
		if not self.t.hasAutoFiller():
			self.logger.setLabel('Does not have auto filler. Nothing to monitor')
			time.sleep(10)
		else:
			self.check_interval = default_interval
			while self.lock:
				print 'while'
				try:
					now_str = self.getNowStr()
					if self.t.getAutoFillerRemainingTime() == -60:
						# when autofiller is set to both room temperature, this value is -60
						self.status = 'idle'
						self.logger.SetLabel('%s Status: %s' % (now_str,self.status))
						time.sleep(snooze_interval)
						continue
					self.checkLevel()
				except Exception as e:
					print e
					self.logger.SetLabel(e)
					break
		return

	def isLowLevel(self):
		if self.loader_level > LOADER_TRIP_LEVEL and  self.column_level > COLUMN_TRIP_LEVEL:
			return False
		else:
			# LN2 level drops during fill.  Check again after expected recovery
			if self.t.isAutoFillerBusy():
				if TESTING:
					print 'wait for recheck'
				time.sleep(RECOVER_TIME)
			self.loader_level = self.t.getRefrigerantLevel(0)
			self.column_level = self.t.getRefrigerantLevel(1)
			return self.loader_level <= LOADER_TRIP_LEVEL or  self.column_level <= COLUMN_TRIP_LEVEL

	def getNowStr(self):
		return datetime.datetime.today().isoformat().split('.')[0]

	def checkLevel(self):
		self.loader_level = self.t.getRefrigerantLevel(0)
		self.column_level = self.t.getRefrigerantLevel(1)
		self.status = 'ok'
		if self.loader_level > LOADER_TRIP_LEVEL and  self.column_level > COLUMN_TRIP_LEVEL:
			# reset check interval to default if recover
			self.check_interval = default_interval
		if self.isLowLevel():
			sendEmail('%s Low level alarm @ %s\nAutoloader level at %d and Column level at %d' % (self.t.name, self.getNowStr(), self.loader_level, self.column_level))
			self.status = 'low'
			self.alarm_tripped += 1
			if self.alarm_tripped >=silent_alarm:
				# snooze longer
				self.check_interval = snooze_interval
				self.alarm_tripped = 0
			else:
				if TESTING and self.check_interval == snooze_interval and not self.t.isAutoFillerBusy():
					tt=threading.Thread(target=self.t.runAutoFiller)
					tt.setDaemon(True)
					tt.start()
		self.logger.SetLabel('%s Status: %s' % (self.getNowStr(),self.status))
		time.sleep(self.check_interval)

# ---------gui---------------
import wx
class MyFrame(wx.Frame):
	def __init__(self, title):
		wx.Frame.__init__(self, None, title=title, pos=(150,150), size=(300,100))

		self.panel = wx.Panel(self,-1)
		sz = wx.GridBagSizer(5, 5)
		heading = wx.StaticText(self.panel, -1, "Most Recent Status")
		self.m_text = wx.StaticText(self.panel, -1, "0000-00-00 00:00:00 Status: Idle")
		#self.m_text.SetSize((300,100))
		sz.Add(heading,(0,0),(1,1),wx.EXPAND|wx.CENTER|wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.m_text,(1,0),(1,1),wx.EXPAND|wx.CENTER|wx.ALIGN_CENTER_VERTICAL)

		sz.AddGrowableCol(0)
		self.SetAutoLayout(True)
		self.panel.SetSizerAndFit(sz)


		self.panel.Centre()
		self.panel.Layout()

		self.monitor = N2Monitor(self.m_text)
		
		self.Bind(wx.EVT_SHOW, self.onShow())
		self.Bind(wx.EVT_CLOSE, self.onClose())

	def onShow(self):
		print 'onShow'
		t = threading.Thread(target=self.monitor.loop, name='monitor')
		t.daemon = True
		t.start()

	def onClose(self):
		print 'onClose'
		self.monitor.lock = True

if __name__=='__main__':
	app = wx.App()
	top = MyFrame("N2 Monitor")
	top.Show()
	app.MainLoop()
