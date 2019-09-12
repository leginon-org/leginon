#!/usr/bin/env python
'''
context mouse and keyboard functions.
'''
import pyautogui

class WindowAutoGui(object):
	def __init__(self, origin):
		self.origin = origin # (x,y)

	def _toScreenPosition(self, position):
		return (self.origin[0]+position[0],self.origin[1]+position[1])

	def clickAtPosition(self, position=(0,0)):
		screen_pos =self._toScreenPosition(position)
		pyautogui.moveTo(screen_pos)
		pyautogui.click()

	def activateWindow(self, position):
		'''
		activate window
		'''
		self.clickAtPosition(position)

class PullDownChoice(WindowAutoGui):
	def __init__(self, origin, pulldown_position=(0,0),item0_position=(0,0),item_height=10,	item_count=1):
		super(PullDownChoice,self).__init__(origin)
		self.pulldown_position = pulldown_position
		self.item0_position = item0_position
		self.item_height = item_height
		self.item_count = item_count

	def select(self, item_index):
		if item_index >= self.item_count:
			raise ValueError('PullDownChoice index exceeds item count')
		# show pull-down
		self.clickAtPosition(self.pulldown_position)
		# select
		pos = (self.item0_position[0], self.item0_position[1]+item_index*self.item_height)
		self.clickAtPosition(pos)

class WindowTypeWrite(WindowAutoGui):
	def write(self, position, text):
		self.clickAtPosition(position)
		pyautogui.typewrite(text)
			
