import smtplib
import email
import email.MIMEImage
import email.MIMEMultipart
import email.MIMEText
import poplib
from PIL import Image
import cStringIO
import NumericImage
import time
import node
#import uidata
import event
import threading

def makeMessage(fromaddress, toaddress, subject,
											text=None, imagestring=None):
	msg = email.MIMEMultipart.MIMEMultipart()
	msg['Subject'] = subject
	msg['From'] = fromaddress
	msg['To'] = toaddress
	msg['Message-ID'] = email.Utils.make_msgid()

	if text is not None:
		mimetext = email.MIMEText.MIMEText(text)
		msg.attach(mimetext)

	if imagestring is not None:
		mimeimage = email.MIMEImage.MIMEImage(imagestring)
		msg.attach(mimeimage)
	return msg

def send(message, hostname=None):
	s = smtplib.SMTP()
	s.connect(hostname)
	fromaddress = message['From']
	toaddress = message['To']
	s.sendmail(fromaddress, [toaddress], message.as_string())
	s.close()

def PILImage2String(pilimage, encoder='JPEG'):
	stream = cStringIO.StringIO()
	pilimage.save(stream, encoder)
	imagestring = stream.getvalue()
	stream.close()
	return imagestring

def NumericImage2String(numericimage, encoder='JPEG'):
	numericimage = NumericImage.Numeric2PILImage(numericimage, scale=True)
	return PILImage2String(numericimage, encoder)

def receive(hostname, username, password):
	pop = poplib.POP3(hostname)
	pop.user(username)
	pop.pass_(password)
	nmessages = len(pop.list()[1])
	messages = []
	for i in range(nmessages):
		messagestring = ''
		for line in pop.retr(i+1)[1]:
			messagestring += line + '\n'
		message = email.message_from_string(messagestring)
		messages.append(message)
	pop.quit()
	return messages

def waitForReply(message, hostname, username, password, interval=10.0):
	while True:
		try:
			replies = map(lambda m: m['In-Reply-To'],
										receive(hostname, username, password))
		except:
			pass
		if message['Message-ID'] in replies:
			return message['Message-ID']
		time.sleep(interval)
	return None

class EmailClient(object):
	def __init__(self, node):
		self.node = node

	def sendAndSet(self, threadingevent, subject, text=None,
													imagestring=None):
		emailevent = event.EmailEvent()
		emailevent['subject'] = subject
		emailevent['text'] = text
		emailevent['image string'] = imagestring
		thread = threading.Thread(target=self.outputEventAndSet,
											args=(emailevent, threadingevent))
		thread.setDaemon(1)
		thread.start()

	def outputEventAndSet(self, oevent, threadingevent):
		try:
			self.node.outputEvent(oevent, wait=True)
			threadingevent.set()
		except node.ConfirmationNoBinding:
			pass

class Email(node.Node):
	eventinputs = node.Node.eventinputs + [event.EmailEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.addEventInput(event.EmailEvent, self.handleEmail)
		self.defineUserInterface()
		self.start()

	def handleEmail(self, ievent):
		self.statusmessage.set('Incoming email send request')
		subject = ievent['subject']
		if subject is None:
			subject = ''
		self.sendAndWaitForReply(subject, ievent['text'], ievent['image string'])
		self.statusmessage.set('Reply received, notifying node')
		self.confirmEvent(ievent)
		self.statusmessage.set('Reply received, node notified')

	def sendAndWaitForReply(self, subject, text=None, imagestring=None):
		fromaddress = self.uifromaddress.get()
		toaddress = self.uitoaddress.get()
		message = makeMessage(fromaddress, toaddress, subject, text, imagestring)
		hostname = self.uioutboundhostname.get()
		self.statusmessage.set('Sending email...')
		send(message, hostname)
		self.waitForReply(message)
		self.statusmessage.set('Reply received')

	def waitForReply(self, message):
		self.statusmessage.set('Email sent, waiting for reply...')
		while True:
			hostname = self.uiinboundhostname.get()
			username = self.uiinboundusername.get()
			password = self.uiinboundpassword.get()
			interval = self.uiinboundinterval.get()
			try:
				messages = receive(hostname, username, password)
				replies = map(lambda m: m['In-Reply-To'], messages)
			except Exception, e:
				self.statusmessage.set('Error in settings: %s' % e)
			else:
				self.statusmessage.set('Email sent, waiting for reply...')
				if message['Message-ID'] in replies:
					return message['Message-ID']
			time.sleep(interval)
		return None

	def testSettings(self):
		hostname = self.uiinboundhostname.get()
		username = self.uiinboundusername.get()
		password = self.uiinboundpassword.get()
		try:
			messages = receive(hostname, username, password)
		except Exception, e:
			self.statusmessage.set('Error in settings: %s' % e)
		else:
			self.statusmessage.set('Settings ok')

	'''
	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.statusmessage = uidata.String('Status', '', 'r')
		statuscontainer = uidata.Container('Status')
		statuscontainer.addObjects((self.statusmessage,))

		self.uifromaddress = uidata.String('From', '', 'rw', persist=True)
		self.uitoaddress = uidata.String('To', '', 'rw', persist=True)
		addresscontainer =  uidata.Container('Addresses')
		addresscontainer.addObjects((self.uifromaddress, self.uitoaddress))

		self.uioutboundhostname = uidata.String('Hostname', '', 'rw', persist=True)
		outboundcontainer = uidata.Container('Outbound')
		outboundcontainer.addObjects((self.uioutboundhostname,))

		self.uiinboundhostname = uidata.String('Hostname', '', 'rw', persist=True)
		self.uiinboundusername = uidata.String('Username', '', 'rw', persist=True)
		self.uiinboundpassword = uidata.Password('Password', '', 'rw',
																							persist=False)
		self.uiinboundinterval = uidata.Integer('Interval', 10, 'rw', persist=True)
		inboundcontainer = uidata.Container('Inbound')
		inboundcontainer.addObjects((self.uiinboundhostname,
																	self.uiinboundusername,
																	self.uiinboundpassword,
																	self.uiinboundinterval))
		testsettingsmethod = uidata.Method('Confirm', self.testSettings)
		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((addresscontainer, outboundcontainer,
																	inboundcontainer, testsettingsmethod))

		container = uidata.LargeContainer('Email')
		container.addObjects((statuscontainer, settingscontainer))
		self.uicontainer.addObject(container)
	'''

if __name__ == '__main__':
	import getpass
	import Numeric

	numericimage = Numeric.ones((256, 256))
	imagestring = NumericImage2String(numericimage)
	message = makeMessage('leginon2@scripps.edu', 'suloway@scripps.edu',
															'testing email', 'this is a test...', imagestring)
	send(message, 'cronus1')
	#username = getpass.getuser()
	username = 'suloway'
	password = getpass.getpass()
	print waitForReply(message, 'mail.scripps.edu', username, password)

