# The Leginon software is Copyright under
# Apache License, Version 2.0
# For terms of the license agreement
# see http://leginon.org
#
# $Source: /ami/sw/cvsroot/pyleginon/leginon.gui.wx/ClickTargetFinder.py,v $
# $Revision: 1.23 $
# $Name: not supported by cvs2svn $
# $Date: 2007-09-18 21:14:00 $
# $Author: vossman $
# $State: Exp $
# $Locker:  $

import wx
import leginon.gui.wx.TargetPanel
import leginon.gui.wx.Settings
import leginon.gui.wx.TargetFinder
import leginon.gui.wx.ToolBar
import leginon.gui.wx.TargetFinder
import leginon.gui.wx.Entry

class Panel(leginon.gui.wx.TargetFinder.Panel):
    icon = 'clicktargetfinder'
    def initialize(self):
        leginon.gui.wx.TargetFinder.Panel.initialize(self)
        self.SettingsDialog = leginon.gui.wx.TargetFinder.SettingsDialog

        self.imagepanel = leginon.gui.wx.TargetPanel.TomoTargetImagePanel(self, -1)
        self.imagepanel.addTargetTool('preview', wx.Colour(255, 128, 255), target=True)
        self.imagepanel.selectiontool.setDisplayed('preview', True)
        self.imagepanel.addTargetTool('acquisition', wx.GREEN, target=True, settings=None, numbers=True,exp=True)
        self.imagepanel.selectiontool.setDisplayed('acquisition', True)
        self.imagepanel.addTargetTool('focus', wx.BLUE, target=True, settings=None,exp=True)
        self.imagepanel.selectiontool.setDisplayed('focus', True)
        self.imagepanel.addTargetTool('track', wx.Colour(135,206,200), shape='x', target=True, settings=None, exp=True)
        self.imagepanel.selectiontool.setDisplayed('track', True)
        self.imagepanel.addTargetTool('reference', wx.Colour(128, 0, 128), target=True, unique=True)
        self.imagepanel.selectiontool.setDisplayed('reference', True)
        self.imagepanel.addTargetTool('done', wx.Colour(218, 0, 0), numbers=True)
        self.imagepanel.selectiontool.setDisplayed('done', True)
        self.imagepanel.addTargetTool('position', wx.Colour(218, 165, 32), shape='x')
        self.imagepanel.selectiontool.setDisplayed('position', True)
        self.imagepanel.addTypeTool('Image', display=True)
        self.imagepanel.selectiontool.setDisplayed('Image', True)
        self.szmain.Add(self.imagepanel, (1, 0), (1, 1), wx.EXPAND)
        self.szmain.AddGrowableRow(1)
        self.szmain.AddGrowableCol(0)

    def onSetImage(self, evt):
        super(Panel,self).onSetImage(evt)       # This sets acquisition vector and beam radius
        try:                                    # Now for focus and track beams
            self.imagepanel.trackimagevectors = self.node.getTrackImageVectors()
            self.imagepanel.trackbeamradius = self.node.getTrackBeamRadius()
            self.imagepanel.focusimagevectors = self.node.getFocusImageVectors()
            self.imagepanel.focusbeamradius = self.node.getFocusBeamRadius()
        except AttributeError:
            # This function is called on initialization and self.node would be None
            pass
            
    def setFocusTargets(self,state,value):
        self.imagepanel.resetFocusTargets(state,value)

    def setTrackTargets(self,value):
        self.imagepanel.resetTrackTargets(value)
    
    def onSettingsTool(self, evt):                      # Override function so that we can use our own SettingsDialog
        dialog = TomoSettingsDialog(self,show_basic=True)
        dialog.ShowModal()
        dialog.Destroy()   

class TomoSettingsDialog(leginon.gui.wx.Settings.Dialog):
    def initialize(self):
        return TomoScrolledSettings(self,self.scrsize,False,self.show_basic)

class TomoScrolledSettings(leginon.gui.wx.TargetFinder.ScrolledSettings):


    def addBasicSettings(self):
      	#self.widgets['user check'] = wx.CheckBox(self, -1,
        #                            'Allow for user verification of selected targets')
    	  self.widgets['queue'] = wx.CheckBox(self, -1,
                                                'Queue up targets')
    	  #self.Bind(wx.EVT_CHECKBOX, self.onUserCheckbox, self.widgets['user check'])
    	  self.Bind(wx.EVT_CHECKBOX, self.onQueueCheckbox, self.widgets['queue'])
    	  sz = wx.GridBagSizer(5, 5)
    	  #sz.Add(self.widgets['user check'], (0, 0), (1, 1),
        #    	wx.ALIGN_CENTER_VERTICAL)
    	  #sz.Add(self.widgets['wait for done'], (1, 0), (1, 1),
        #        wx.ALIGN_CENTER_VERTICAL)
    	  sz.Add(self.widgets['queue'], (1, 0), (1, 1),
            	wx.ALIGN_CENTER_VERTICAL)
    	  return sz

    def addSettings(self):
        #self.widgets['wait for done'] = wx.CheckBox(self, -1,
        #            'Wait for another node to process targets before marking them done')
        #self.widgets['user check'] = wx.CheckBox(self, -1,
        #                                                            'Allow for user verification of selected targets')
        #checkmethodsz = self.createCheckMethodSizer()
        self.widgets['queue'] = wx.CheckBox(self, -1,
                                                                                            'Queue up targets')
        self.widgets['queue drift'] = wx.CheckBox(self, -1, 'Declare drift when queue submitted')
        self.widgets['sort target'] = wx.CheckBox(self, -1, 'Sort targets by shortest path')
        #self.widgets['allow append'] = wx.CheckBox(self, -1, 'Allow target finding on old images')
        self.widgets['multifocus'] = wx.CheckBox(self, -1, 'Use all focus targets for averaging')
        self.widgets['allow no focus'] = wx.CheckBox(self, -1, 'Do not require focus targets in user verification')
        self.widgets['auto focus target'] = wx.CheckBox(self,-1,
                                                        'Place focus target automatically')
        #self.widgets['auto track target'] = wx.CheckBox(self,-1,
        #                                                'Place tracking target automatically')
        self.widgets['focus target offset'] = leginon.gui.wx.Entry.FloatEntry(self, -1) 
        self.widgets['track target offset'] = leginon.gui.wx.Entry.FloatEntry(self, -1)
        
        self.widgets['tomo beam diameter'] = leginon.gui.wx.Entry.FloatEntry(self, -1)
        self.widgets['focus beam diameter'] = leginon.gui.wx.Entry.FloatEntry(self, -1) 
        self.widgets['track beam diameter'] = leginon.gui.wx.Entry.FloatEntry(self, -1)
        
        self.widgets['stretch tomo beam'] = wx.CheckBox(self,-1,
                                                'Stretch tomo beam size along tilt axis')
        self.widgets['stretch focus beam'] = wx.CheckBox(self,-1,
                                                'Stretch focus beam size along tilt axis')
        self.widgets['stretch track beam'] = wx.CheckBox(self,-1,
                                                'Stretch track beam size along tilt axis')

        #self.Bind(wx.EVT_CHECKBOX, self.onUserCheckbox, self.widgets['user check'])
        self.Bind(wx.EVT_CHECKBOX, self.onQueueCheckbox, self.widgets['queue'])
        self.Bind(wx.EVT_CHECKBOX, self.onAutoFocusTargetCheckbox,self.widgets['auto focus target'])
        self.Bind(leginon.gui.wx.Entry.EVT_ENTRY, self.onFocusTargetOffset,self.widgets['focus target offset'])
        self.Bind(leginon.gui.wx.Entry.EVT_ENTRY, self.onTrackTargetOffset,self.widgets['track target offset'])

        sz = wx.GridBagSizer(15, 15)
        #sz.Add(self.widgets['user check'], (0, 0), (1, 1),
        #                wx.ALIGN_CENTER_VERTICAL)
        #sz.Add(checkmethodsz, (1, 0), (1, 1),
        #                wx.ALIGN_CENTER_VERTICAL)
        #sz.Add(self.widgets['wait for done'], (1, 0), (1, 1),
        #                wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.widgets['queue'], (2, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.widgets['queue drift'], (3, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.widgets['sort target'], (4, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.widgets['multifocus'], (5, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.widgets['allow no focus'], (6, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)
        sz.Add(self.widgets['auto focus target'], (7, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)
        
        focus_label = wx.StaticText(self, -1, 'focus target offset in meters')
        sz.Add(focus_label, (8, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.LEFT,10)
        sz.Add(self.widgets['focus target offset'], (8, 1), (1, 1), 
               wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        track_label = wx.StaticText(self, -1, 'track target offset in meters')
        sz.Add(track_label, (9, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.LEFT,10)
        sz.Add(self.widgets['track target offset'], (9, 1), (1, 1),
                        wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        tomo_beam_label = wx.StaticText(self, -1, 'diameter of tomo beam in meters')
        sz.Add(tomo_beam_label, (10, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.LEFT,10)
        sz.Add(self.widgets['tomo beam diameter'], (10, 1), (1, 1),
                        wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        focus_beam_label = wx.StaticText(self, -1, 'diameter of focus beam in meters')
        sz.Add(focus_beam_label, (11, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.LEFT,10)
        sz.Add(self.widgets['focus beam diameter'], (11, 1), (1, 1),
                        wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
        
        track_beam_label = wx.StaticText(self, -1, 'diameter of track beam in meters')
        sz.Add(track_beam_label, (12, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.LEFT,10)
        sz.Add(self.widgets['track beam diameter'], (12, 1), (1, 1),
                        wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)

        sz.Add(self.widgets['stretch tomo beam'], (13, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)

        sz.Add(self.widgets['stretch focus beam'], (14, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)
        
        sz.Add(self.widgets['stretch track beam'], (15, 0), (1, 1),
                        wx.ALIGN_CENTER_VERTICAL)
        
        #if not hide_incomplete:
        #    sz.Add(self.widgets['allow append'], (7, 0), (1, 1),
        #                    wx.ALIGN_CENTER_VERTICAL)
    
        return sz
    
    def onAutoFocusTargetCheckbox(self, evt):
        state = evt.IsChecked()
        value = self.widgets['focus target offset'].GetValue()
        if value is not None:
            self.panel.setFocusTargets(state,value)

    def onFocusTargetOffset(self,evt):
        state = self.widgets['auto focus target'].GetValue()
        value = evt.GetValue()
        if value is not None:
            self.panel.setFocusTargets(state,value)
    
    def onTrackTargetOffset(self,evt):
        value = evt.GetValue()
        if value is not None:
            self.panel.setTrackTargets(value)
    
        
        
           
if __name__ == '__main__':
    class App(wx.App):
        def OnInit(self):
            frame = wx.Frame(None, -1, 'Click Target Finder Test')
            panel = Panel(frame, 'Test')
            frame.Fit()
            self.SetTopWindow(frame)
            frame.Show()
            return True

    app = App(0)
    app.MainLoop()

