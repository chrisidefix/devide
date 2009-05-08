#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# generated by wxGlade 0.6.3 on Fri May 08 10:38:56 2009

import wx

# begin wxGlade: extracode
# end wxGlade



class aboutDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: aboutDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.toplevel_panel = wx.Panel(self, -1)
        self.sizer_5_staticbox = wx.StaticBox(self.toplevel_panel, -1, "Component Versions")
        self.name_version_text = wx.StaticText(self.toplevel_panel, -1, "DeVIDE v8.2.0000", style=wx.ALIGN_CENTRE)
        self.icon_bitmap = wx.StaticBitmap(self.toplevel_panel, -1, wx.NullBitmap)
        self.label_2 = wx.StaticText(self.toplevel_panel, -1, "DeVIDE is copyright (c) 2002-2009 Charl P. Botha, TU Delft\nAll rights reserved.  See COPYRIGHT for details.\n\nSignificant contributions by:\nJoris van Zwieten, Stef Busking, Emiel van IJsseldijk, Peter Krekel.\n\nhttp://visualisation.tudelft.nl/Projects/DeVIDE", style=wx.ALIGN_CENTRE)
        self.versions_listbox = wx.ListBox(self.toplevel_panel, -1, choices=[], style=wx.LB_NEEDED_SB)
        self.button_1 = wx.Button(self.toplevel_panel, wx.ID_OK, "OK")

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: aboutDialog.__set_properties
        self.SetTitle("About DeVIDE")
        self.name_version_text.SetFont(wx.Font(16, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.icon_bitmap.SetMinSize((64, 64))
        self.versions_listbox.SetMinSize((350, 200))
        self.button_1.SetDefault()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: aboutDialog.__do_layout
        toplevel_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.BoxSizer(wx.VERTICAL)
        sizer_5 = wx.StaticBoxSizer(self.sizer_5_staticbox, wx.VERTICAL)
        sizer_4.Add(self.name_version_text, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer_4.Add(self.icon_bitmap, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 10)
        sizer_4.Add(self.label_2, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer_5.Add(self.versions_listbox, 1, wx.ALL|wx.EXPAND, 4)
        sizer_4.Add(sizer_5, 1, wx.TOP|wx.BOTTOM|wx.EXPAND, 7)
        sizer_4.Add(self.button_1, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_2.Add(sizer_4, 1, wx.ALL|wx.EXPAND, 7)
        self.toplevel_panel.SetSizer(sizer_2)
        toplevel_sizer.Add(self.toplevel_panel, 1, wx.EXPAND, 0)
        self.SetSizer(toplevel_sizer)
        toplevel_sizer.Fit(self)
        self.Layout()
        # end wxGlade

# end of class aboutDialog


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    dialog_1 = aboutDialog(None, -1, "")
    app.SetTopWindow(dialog_1)
    dialog_1.Show()
    app.MainLoop()
