#!/usr/bin/env python
"""
Automatically create a session using the same project,
Leginon clients, presets, and application of the most recent session
from the same host.
"""
import sys
from leginon import leginondata
from leginon import autoscreen
from leginon import settingsfun
import time
from pyami import mysocket

def start(sessionname, clientlist, gridslot,z, task=None):
	if clientlist:
		clients = ','.join(clientlist)
	else:
		clients = None
	if gridslot:
		gridslot = '%d' % gridslot
	else:
		gridslot = None
	if not gridslot:
		z = None
	option_dict = {'version':None, 'session': sessionname, 'clients': clients,'prevapp':True, 'gridslot':gridslot, 'stagez':z, 'task':task}
	# options need to be set as attributes
	options = autoscreen.Options()
	for k in option_dict.keys():
		setattr(options,k,option_dict[k])
	from leginon import start
	start.start(options)

def getOldSessionNameOnHost():
	myhost = mysocket.gethostname().lower()
	try:
		r = leginondata.ConnectToClientsData(localhost=myhost).query(results=1)[0]
	except:
		try:
			answer = input('Enter an old session name to base new sessions on: ')
			s = leginondata.SessionData(name=answer).query(results=1)[0]
			r = leginondata.ConnectToClientsData(session=s).query(results=1)[0]
		except Exception as e:
			print('Error: session %s does not exist' % answer)
			sys.exit(1)
		if r['localhost'] != myhost:
			print('Error: The old session (from %s) is not started on this host (%s).' % (r['localhost'], myhost))
			sys.exit(1)
	return r['session']['name']
	
if __name__ == "__main__":
	grid_info_map = []
	use_gui = True
	# current slot
	slots = [0,]
	for s in slots:
		grid_info_map.append({'slot_number':int(s),'comment':'','project_id':None})
	# old session
	answer = getOldSessionNameOnHost()
	app1 = autoscreen.SessionSetCreator()
	try:
		app1.saveAutoSessionSet(answer)
	except Exception as e:
		print('Error: %s' % e)
		sys.exit(1)
	# z value
	stagez = app1.getOldSessionStageZ()
	zanswer = input('Enter Z stage height to return to in um (default: the old sessionvalue %.1f): ' % (stagez*1e6,))
	if zanswer != '':
		try:
			stagez = float(zanswer)*1e-6
		except ValueError:
			print('Invalid number entry: %s' % zanswer)
			sys.exit(1)
	# confirm session project assignment
	if use_gui:
		app1.confirmCommentProjectWithGui(grid_info_map)
	else:
		app1.setGridMap(grid_info_map)

	if app1.all_grid_info == False:
		sys.exit(1)
	# create by the order of the confirmed all_grid_info
	# app.all_grid_info may have been modified by the gui.
	slot_order = map((lambda x:x['slot_number']),app1.all_grid_info)
	task_order = []

	# SessionData are created before starting.
	app2 = autoscreen.SessionCreator(app1.session_set)
	for i, slot_number in enumerate(slot_order):
		# project_id and comment are set before creating the session
		app2.setProjectId(app1.all_grid_info[i]['project_id'])
		app2.setComment(app1.all_grid_info[i]['comment'])
		app2.createSession()
		# create gridhook link in grid server
		app2.linkGridServerSession(is_auto_session=False)
		if i == 0:
			first_session = app2.session
			first_slot = slot_number
			# copy the last settings from the old session instead of most recent user settings.
			launched_app = app2.launched_app
			app3 = autoscreen.SessionSettingsCopier(first_session, app2.old_session, launched_app['application'])
		time.sleep(1.0) # to prevent session out of order on the viewer.
	#start the first session.  The rest will be set from Manager.
	start(first_session['name'],app2.clients,first_slot,stagez, None)
