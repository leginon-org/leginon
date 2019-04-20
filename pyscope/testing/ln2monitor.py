
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
try:
	# wxpython 2.8
	from wx.lib.pubsub import Publisher
	pub = Publisher()
	is_wx28 = True
except:
	# wxpython 2.9 and up
	from wx.lib.pubsub import pub 
	is_wx28 = False
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
	def __init__(self):
		self.t = instrumenttype.getInstrumentTypeInstance('tem')
		self.alarm_tripped = 0
		self.lock = True
		self.status = 'ok'

	def loop(self):
		if not self.t.hasAutoFiller():
			self.sendLabel('Does not have auto filler. Nothing to monitor')
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
						self.sendLabel('%s Status: %s' % (now_str,self.status))
						time.sleep(snooze_interval)
						continue
					self.checkLevel()
				except Exception as e:
					self.lock = False
					print e
					break
		return

	def sendLabel(self, text):
		# thread safe way to update wx value
		wx.CallAfter(self._sendLabel, text)

	def _sendLabel(self, text):
		# thread safe way to update wx value
		if is_wx28:
			pub.sendMessage("update", text)
		else:
			pub.sendMessage("update", msg=text)

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
			if self.alarm_tripped:
				print 'reset'
				self.alarm_tripped = 0
		if self.isLowLevel():
			self.alarm_tripped += 1
			if self.alarm_tripped == 1:
				sendEmail('%s Low level alarm @ %s\nAutoloader level at %d and Column level at %d' % (self.t.name, self.getNowStr(), self.loader_level, self.column_level))
			self.status = 'low'
			if self.alarm_tripped >=silent_alarm:
				# snooze longer
				self.check_interval = snooze_interval
				print 'start to snooze'
				if TESTING and not self.t.isAutoFillerBusy():
					tt=threading.Thread(target=self.t.runAutoFiller)
					tt.daemon = True
					tt.start()
		self.sendLabel('%s Status: %s' % (self.getNowStr(),self.status))
		time.sleep(self.check_interval)

# ---------gui---------------
import wx
class MyFrame(wx.Frame):
	def __init__(self, title):
		wx.Frame.__init__(self, None, title=title, pos=(150,150), size=(300,100))

		self.panel = wx.Panel(self,-1)
		sz = wx.GridBagSizer(5, 5)
		if TESTING:
			alarm='Testing'
		else:
			alarm='Emailing'
		heading = wx.StaticText(self.panel, -1, "State:")
		alarm_type = wx.StaticText(self.panel, -1, "Alarm:%s" % alarm)
		self.m_text = wx.StaticText(self.panel, -1, "0000-00-00 00:00:00 Status: Idle")
		#self.m_text.SetSize((300,100))
		sz.Add(heading,(0,0),(1,1),wx.LEFT|wx.ALIGN_CENTER_VERTICAL)
		sz.Add(alarm_type,(0,1),(1,1),wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		sz.Add(self.m_text,(1,0),(1,2),wx.EXPAND|wx.CENTER|wx.ALIGN_CENTER_VERTICAL)
		self.SetAutoLayout(True)
		self.panel.SetSizerAndFit(sz)


		self.panel.Centre()
		self.panel.Layout()

		pub.subscribe(self.updateLabel, "update")

		self.monitor = N2Monitor()
		
		self.Bind(wx.EVT_SHOW, self.onShow())

	def updateLabel(self, msg):
		if is_wx28:
			text = msg.data
		else:
			text = msg
		self.m_text.SetLabel(text)

	def onShow(self):
		t = threading.Thread(target=self.monitor.loop, name='monitor')
		t.daemon = True
		t.start()

if __name__=='__main__':
	# redirect=False sends stdout/stderr to console.  Needed on Windows to make
	# sure threads are stopped when MyFrame is closed.  Otherwise the
	# stdout window keeps the thread alive and cause problem when the thread
	# is trying to update the dead MyFrame.
	app = wx.App(redirect=False)
	top = MyFrame("N2 Monitor")
	top.Show()
	app.MainLoop()
