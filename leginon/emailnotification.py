import smtplib
import email
import email.MIMEMultipart
import email.MIMEImage
import poplib
import sha

def emailpicture(fromaddress, toaddress, subject, files):
	msg = email.MIMEMultipart.MIMEMultipart()
	msg['Subject'] = subject
	msg['From'] = fromaddress
	msg['To'] = toaddress

	for filename in [files]:
		f = open(filename, 'rb')
		imagestring = f.read()
		print sha.new(imagestring).hexdigest()
		image = email.MIMEImage.MIMEImage(imagestring)
		f.close()
		msg.attach(image)

	s = smtplib.SMTP()
	s.connect()
	s.sendmail(fromaddress, [toaddress], msg.as_string())
	s.close()

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
	emailpicture('leginon2@scripps.edu', 'suloway@scripps.edu',
								'testing email', 'robotgridtray.png')
	username = getpass.getuser()
	password = getpass.getpass()
	messages = get('mail.scripps.edu', username, password)
	for message in messages:
		print message['From']
		print message['To']
		print message['Subject']
		print message.get_payload()

