#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Mon Apr 27 17:59:37 2009

import wx

# begin wxGlade: extracode
from external.ObjectListView import ObjectListView

from external.ObjectListView import ObjectListView

# end wxGlade



class CoMedIControlsFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: CoMedIControlsFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.main_panel = wx.Panel(self, -1)
        self.comparison_mode_notebook = wx.Notebook(self.main_panel, -1, style=0)
        self.match_mode_notebook = wx.Notebook(self.main_panel, -1, style=0)
        self.notebook_pane_ssl = wx.Panel(self.match_mode_notebook, -1)
        self.sizer_7_staticbox = wx.StaticBox(self.main_panel, -1, "Match Mode")
        self.sizer_6_staticbox = wx.StaticBox(self.main_panel, -1, "Comparison Mode")
        self.sizer_4_staticbox = wx.StaticBox(self.main_panel, -1, "General")
        self.label_1 = wx.StaticText(self.main_panel, -1, "Current 3D cursor")
        self.cursor_text = wx.TextCtrl(self.main_panel, -1, "")
        self.label_2 = wx.StaticText(self.notebook_pane_ssl, -1, "Source landmarks")
        self.source_landmarks_olv = ObjectListView(self.notebook_pane_ssl, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.label_3 = wx.StaticText(self.notebook_pane_ssl, -1, "Target landmarks")
        self.target_landmarks_olv = ObjectListView(self.notebook_pane_ssl, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.lm_add_button = wx.Button(self.notebook_pane_ssl, -1, "Add")
        self.lm_move_button = wx.Button(self.notebook_pane_ssl, -1, "Move")
        self.lm_delete_button = wx.Button(self.notebook_pane_ssl, -1, "Delete")
        self.notebook_1_pane_1 = wx.Panel(self.comparison_mode_notebook, -1)
        self.notebook_1_pane_2 = wx.Panel(self.comparison_mode_notebook, -1)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: CoMedIControlsFrame.__set_properties
        self.SetTitle("frame_1")
        self.lm_add_button.SetToolTipString("Add landmark at current 3D cursor.")
        self.lm_move_button.SetToolTipString("Move currently selected landmark to current 3D cursor.")
        self.lm_delete_button.SetToolTipString("Delete currently selected landmark.")
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: CoMedIControlsFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_6 = wx.StaticBoxSizer(self.sizer_6_staticbox, wx.VERTICAL)
        sizer_7 = wx.StaticBoxSizer(self.sizer_7_staticbox, wx.VERTICAL)
        sizer_8 = wx.BoxSizer(wx.VERTICAL)
        sizer_10 = wx.BoxSizer(wx.VERTICAL)
        sizer_9 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.StaticBoxSizer(self.sizer_4_staticbox, wx.VERTICAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5.Add(self.label_1, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 4)
        sizer_5.Add(self.cursor_text, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_4.Add(sizer_5, 0, wx.BOTTOM|wx.EXPAND, 7)
        sizer_3.Add(sizer_4, 0, wx.EXPAND, 0)
        sizer_10.Add(self.label_2, 0, 0, 0)
        sizer_10.Add(self.source_landmarks_olv, 1, wx.BOTTOM|wx.EXPAND, 7)
        sizer_10.Add(self.label_3, 0, 0, 0)
        sizer_10.Add(self.target_landmarks_olv, 1, wx.BOTTOM|wx.EXPAND, 7)
        sizer_9.Add(self.lm_add_button, 0, 0, 0)
        sizer_9.Add(self.lm_move_button, 0, 0, 0)
        sizer_9.Add(self.lm_delete_button, 0, 0, 0)
        sizer_10.Add(sizer_9, 0, wx.ALIGN_RIGHT, 0)
        sizer_8.Add(sizer_10, 1, wx.ALL|wx.EXPAND, 7)
        self.notebook_pane_ssl.SetSizer(sizer_8)
        self.match_mode_notebook.AddPage(self.notebook_pane_ssl, "Single Structure Landmarks")
        sizer_7.Add(self.match_mode_notebook, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_7, 2, wx.EXPAND, 0)
        self.comparison_mode_notebook.AddPage(self.notebook_1_pane_1, "Data 2 Matched")
        self.comparison_mode_notebook.AddPage(self.notebook_1_pane_2, "Checkerboard")
        sizer_6.Add(self.comparison_mode_notebook, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_6, 1, wx.EXPAND, 0)
        sizer_2.Add(sizer_3, 1, wx.ALL|wx.EXPAND, 7)
        self.main_panel.SetSizer(sizer_2)
        sizer_1.Add(self.main_panel, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade

# end of class CoMedIControlsFrame


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = CoMedIControlsFrame(None, -1, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()