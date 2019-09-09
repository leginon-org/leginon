#!/usr/bin/env python
'''
context mouse and keyboard functions.
'''
import pyautogui

class WindowAutoGui(object):
	def __init__(self, origin):
		self.origin = origin # (x,y)

	def _toScreenPosition(position):
		return (origin[0]+position[0],origin[1]+position[1])

	def clickAtPosition(self, position=(0,0)):
		screen_pos =self._toScreenPosition(position)
		pyautogui.move(screen_pos)
		pyautogui.click()

class PullDownChoice(WindowAutoGui)
	def __init__(self, origin, activate_position=(0,0),item0_position=(0,0),item_height=10,	item_count=1):
		super(PullDownChoice,self).__init__(origin)

	def select(self, item_index):
		if item_index >= item_count:
			raise ValueError('PullDownChoice index exceeds item count')
		# activate
		self.clickAtPosition(activate_position)
		# select
		pos = (item0_position[0], item0_position[1]+item_index*item_height)
		self.clickAtPosition(pos)

class WindowTypeWrite(WindowAutoGui)
	def write(self, position, text):
		self.clickAtPosition(position)
		pyautogui.typewrite(text)
			
