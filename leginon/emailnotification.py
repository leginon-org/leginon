import smtplib
import email
import email.MIMEMultipart
import email.MIMEImage
import poplib
import sha
import Image
import cStringIO

def emailImageString(fromaddress, toaddress, subject, imagestring):
	msg = email.MIMEMultipart.MIMEMultipart()
	msg['Subject'] = subject
	msg['From'] = fromaddress
	msg['To'] = toaddress

	print sha.new(imagestring).hexdigest()
	image = email.MIMEImage.MIMEImage(imagestring)
	msg.attach(image)

	s = smtplib.SMTP()
	s.connect()
	s.sendmail(fromaddress, [toaddress], msg.as_string())
	s.close()

def pilimage2jpgstring(pilimage):
	stream = cStringIO.StringIO()
	pilimage.save(stream, 'JPEG')
	imagestring = stream.getvalue()
	stream.close()
	return imagestring

def emailPILImage(fromaddress, toaddress, subject, pilimage):
	emailImageString(fromaddress, toaddress, subject,
										pilimage2jpgstring(pilimage))

def get(hostname, username, password):
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

if __name__ == '__main__':
	import getpass

	pilimage = Image.open('test1.jpg')
	emailPILImage('leginon2@scripps.edu', 'suloway@scripps.edu',
								'testing email', pilimage)
	username = getpass.getuser()
	password = getpass.getpass()
	messages = get('mail.scripps.edu', username, password)
	for message in messages:
		print message['From']
		print message['To']
		print message['Subject']
		print message.get_payload()

