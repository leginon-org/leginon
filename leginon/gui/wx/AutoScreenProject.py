# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#

import wx
import threading

class ScreenInfoMap(wx.Frame):
	'''
	Gui to set project and session comment for autoscreening
	'''
	def __init__(self, node, old_session, old_project, allmap_info, allproject_info):
		title = 'test screen info'
		super(ScreenInfoMap, self).__init__(None, title=title, size=(300,800))
		panel = wx.Panel(self)
		self.node = node
		sb = wx.StaticBox(self, -1, 'auto screen order list')
		self.sbsz = wx.StaticBoxSizer(sb, wx.VERTICAL)
		self.pagesizer = wx.GridBagSizer(5,5)
		self.sizer = wx.GridBagSizer(5,5)
		self.sbsz.Add(self.sizer, 1, wx.EXPAND|wx.ALL, 5)
		self.szbottom = wx.GridBagSizer(5, 5)
		self.szbuttons = wx.GridBagSizer(5,5)
		self.buttons = {} 

		self.sizer.Add(wx.StaticText(self, -1, 'Slot #'), (0, 0), (1, 1))
		self.sizer.Add(wx.StaticText(self, -1, 'Session Comment'), (0,1), (1, 1))
		self.sizer.Add(wx.StaticText(self, -1, 'Project'), (0, 2), (1, 1))

		self.projects = allproject_info
		self.gridsizers = []
		self.sz_slot_numbers = []
		self.sz_choices = []
		self.sz_comments = []
		self.project_choices = map((lambda x: x['name']),self.projects)
		self.project_ids = map((lambda x: x.dbid),self.projects)
		self.default_project_index = self.project_ids.index(old_project.dbid)
		for i in range(len(allmap_info)):
			self.addGridMapping(i, allmap_info[i])


		self.sizer.AddGrowableCol(1)
		self.sizer.AddGrowableCol(2)
		self.pagesizer.Add(self.sbsz, (0, 0), (1, 1), wx.EXPAND|wx.ALL,10)
		self.pagesizer.AddGrowableRow(0)
		self.pagesizer.AddGrowableCol(0)

		self.onInitialize()
		self.szbottom.Add(wx.StaticText(self, -1,
									'press the "Save" button to run.'), (0, 0), (1, 1))
		self.szbottom.Add(self.szbuttons, (1, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALL, 10)
		self.szbottom.AddGrowableCol(0)
		self.pagesizer.Add(self.szbottom, (1, 0), (1, 1), wx.EXPAND|wx.ALL)

		self.SetSizerAndFit(self.pagesizer)
		self.Show()

	def addGridMapping(self, i, grid_info):
		'''
		add a row of grid info sizers
		'''
		self.sz_slot_numbers.append(wx.StaticText(self, -1, '%d' % grid_info['slot_number']))
		self.sz_comments.append(wx.TextCtrl(self, -1, grid_info['comment'], size=wx.Size(-1,50)))
		self.sz_choices.append(wx.Choice(self, -1, choices=self.project_choices))
		# select default project
		if grid_info['project_id'] is None:
			self.sz_choices[i].SetSelection(self.default_project_index)
		else:
			self.sz_choices[i].SetSelection(self.project_ids.index(grid_info['project_id']))
		self.sizer.Add(self.sz_slot_numbers[i], (1+i, 0), (1, 1),
														wx.ALIGN_CENTER_VERTICAL)
		self.sizer.Add(self.sz_comments[i], (1+i, 1), (1, 1),
														wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
		self.sizer.Add(self.sz_choices[i], (1+i, 2), (1, 1),
														wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

	def onSave(self, event):
		all_grid_info = []
		for i in range(len(self.sz_choices)):
			slot_number = int(self.sz_slot_numbers[i].GetLabel())
			comment=self.sz_comments[i].GetLineText(0)
			project_id=self.project_ids[self.sz_choices[i].GetSelection()]
			all_grid_info.append({'slot_number':slot_number, 'comment':comment, 'project_id':project_id})
		# set grid map info if called from autoscreeen.py
		if self.node:
			t=threading.Thread(target=self.node.uiSetGridMap,args=(all_grid_info,))
			t.start()
			t.join()
		else:
			print(all_grid_info)
		self.Close()

	def onAbort(self, event):
		if self.node:
			t=threading.Thread(target=self.node.uiSetGridMap,args=(False,))
			t.start()
			t.join()
		self.Close()

	def addButton(self, label, id=-1, flags=None):
		col = len(self.buttons)
		self.buttons[label] = wx.Button(self, id, label)
		if flags is None:
			if col > 0:
				flags = wx.ALIGN_CENTER
			else:
				flags = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT
		self.szbuttons.Add(self.buttons[label], (0, col), (1, 1), flags)
		return self.buttons[label]

	def onInitialize(self):
		self.bsave = self.addButton('&Save')
		self.babort = self.addButton('&Abort')
		self.Bind(wx.EVT_BUTTON, self.onSave, self.bsave)
		self.Bind(wx.EVT_BUTTON, self.onAbort, self.babort)

class FakeData(dict):
	def __init__(self,dbid):
		self.dbid = dbid

if __name__=='__main__':
	# Testing with fake data
	p1 = FakeData(1)
	p1['name']='test1'
	p2 = FakeData(2)
	p2['name']='test2'
	allproject_info = [p1,p2]
	old_project = p1
	old_session = {'name':'old_session'}
	allmap_info = [
						{'slot_number':1,'comment':'my test1','project_id':None},
						{'slot_number':2,'comment':'my test2','project_id':2},
	]

	app = wx.App()
	ScreenInfoMap(None, old_session, old_project, allmap_info, allproject_info)
	app.MainLoop()
