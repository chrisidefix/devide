# $Id: vtk_dicom_rdr.py,v 1.4 2002/08/19 15:30:59 cpbotha Exp $

import gen_utils
import os
from module_base import \
     module_base, \
     module_mixin_vtk_pipeline_config, \
     module_mixin_fo_dialog
import stat
from wxPython.wx import *
from wxPython.xrc import *
import vtk
import vtkcpbothapython
import module_utils

class vtk_dicom_rdr(module_base,
                  module_mixin_vtk_pipeline_config,
                  module_mixin_fo_dialog):
    
    def __init__(self, module_manager):
        # call the constructor in the "base"
        module_base.__init__(self, module_manager)

        # setup necessary VTK objects
	self._reader = vtkcpbothapython.vtkDICOMVolumeReader()
        self._reader.DebugOn()

        # this part of the config is stored in this module, and not in
        # the reader.
        self._dicom_dirname = None
        self._dicom_filenames = []

        # following is the standard way of connecting up the dscas3 progress
        # callback to a VTK object; you should do this for all objects in
        # your module
        self._reader.SetProgressText('Reading DICOM data')
        mm = self._module_manager
        self._reader.SetProgressMethod(lambda s=self, mm=mm:
                                       mm.vtk_progress_cb(s._reader))
	
        self._view_frame = None
        self.create_view_window()
	self.sync_config()
	
    def close(self):
        self._view_frame.Destroy()
	if hasattr(self, '_reader'):
	    del self._reader

    def get_input_descriptions(self):
	return ()
    
    def set_input(self, idx, input_stream):
	raise Exception
    
    def get_output_descriptions(self):
	return (self._reader.GetOutput().GetClassName(),)
    
    def get_output(self, idx):
	return self._reader.GetOutput()
    
    def sync_config(self):
        if self._dicom_dirname:
            self._view_frame.dirname_text.SetValue(self._dicom_dirname)
        else:
            self._view_frame.dirname_text.SetValue("")
	
    def apply_config(self):
        # get a list of files in the indicated directory, stuff them all
        # into the dicom reader
        self._dicom_dirname = self._view_frame.dirname_text.GetValue()

        if self._dicom_dirname == None:
            return
        try:
            filenames_init = os.listdir(self._dicom_dirname)
        except Exception, e:
            gen_utils.log_error('Could not read DICOM directory: %s' % e)

        # go through list of files in directory, perform trivial tests
        # and create a new list of files 
        dicom_fullnames = []
        for filename in filenames_init:
            # make full filename
            fullname = os.path.join(self._dicom_dirname, filename)
            # at the moment, we check that it's a regular file
            if stat.S_ISREG(os.stat(fullname)[stat.ST_MODE]):
                dicom_fullnames.append(fullname)

        if len(dicom_fullnames) == 0:
            wxLogError('Empty directory specified, not attempting '
                       'change in config.')
            return

        # this will clear only the dicom_filenames_buffer without setting
        # mtime of the vtkDICOMVolumeReader
        self._reader.clear_dicom_filenames()

        for fullname in dicom_fullnames:
            # this will simply add a file to the buffer list of the
            # vtkDICOMVolumeReader (will not set mtime)
            print "%s\n" % fullname
            self._reader.add_dicom_filename(fullname)
        
        # if we've added the same list as we added at the previous exec
        # of apply_config(), the dicomreader is clever enough to know that
        # it doesn't require an update.  Yay me.

    def execute_module(self):
        # get the vtkDICOMVolumeReader to try and execute
	self._reader.Update()
        # tell the vtk log file window to poll the file; if the file has
        # changed, i.e. vtk has written some errors, the log window will
        # pop up.  you should do this in all your modules right after you
        # caused some VTK processing which might have resulted in VTK
        # outputting to the error log
        self._module_manager.vtk_poll_error()

    def create_view_window(self):
        parent_window = self._module_manager.get_module_view_parent_window()
        self._view_frame = vtk_dicom_rdr_view_frame(parent=parent_window,
                                                    id=-1, title='null')
        
        EVT_CLOSE(self._view_frame,
                  lambda e, s=self: s._view_frame.Show(false))

        EVT_BUTTON(self._view_frame, self._view_frame.BROWSE_BUTTON_ID,
                   self.dn_browse_cb)
        EVT_CHOICE(self._view_frame, self._view_frame.VTK_OBJECT_CHOICE_ID,
                   self.vtk_object_choice_cb)
        EVT_BUTTON(self._view_frame, self._view_frame.VTK_PIPELINE_ID,
                   self.vtk_pipeline_cb)

        module_utils.bind_CSAEO2(self, self._view_frame)

        # bind events to the standard cancel, sync, apply, execute, ok buttons
#        module_utils.bind_CSAEO(self, self._view_frame)



    def view(self, parent_window=None):
	# first make sure that our variables agree with the stuff that
        # we're configuring
	self.sync_config()
        self._view_frame.Show(true)
        
    def dn_browse_cb(self, event):
        path = self.dn_browse(self._view_frame,
                              "Choose a DICOM directory",
                              self._module_manager.get_app_dir())

        if path != None:
            self._view_frame.dirname_text.SetValue(path)

    def vtk_object_choice_cb(self, event):
        if self._view_frame.object_choice.GetStringSelection() == \
           'vtkDICOMVolumeReader':
            self.vtk_object_configure(self._view_frame, None, self._reader)

    def vtk_pipeline_cb(self, event):
        # move this to module utils too, or to base...
        self.vtk_pipeline_configure(self._view_frame, None, (self._reader,))
	    
# wxGlade generated code ----------------------------------------------------

class vtk_dicom_rdr_view_frame(wxFrame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: __init__
        kwds["style"] = wxCAPTION|wxMINIMIZE_BOX|wxMAXIMIZE_BOX|wxSYSTEM_MENU|wxRESIZE_BORDER
        wxFrame.__init__(self, *args, **kwds)
        self.sizer_1 = wxBoxSizer(wxVERTICAL)
        self.sizer_2 = wxBoxSizer(wxHORIZONTAL)
        self.ok_button = wxButton(self, wxID_OK, "OK", size=(-1, -1))
        self.EXECUTE_ID  =  wxNewId()
        self.execute_button = wxButton(self, self.EXECUTE_ID , "Execute", size=(-1, -1))
        self.APPLY_ID  =  wxNewId()
        self.apply_button = wxButton(self, self.APPLY_ID , "Apply", size=(-1, -1))
        self.SYNC_ID  =  wxNewId()
        self.sync_button = wxButton(self, self.SYNC_ID , "Sync", size=(-1, -1))
        self.cancel_button = wxButton(self, wxID_CANCEL, "Cancel", size=(-1, -1))
        self.sizer_4 = wxBoxSizer(wxHORIZONTAL)
        self.VTK_PIPELINE_ID  =  wxNewId()
        self.pipeline_button = wxButton(self, self.VTK_PIPELINE_ID , "Pipeline", size=(-1, -1))
        self.label_3 = wxStaticText(self, -1, "or", size=(-1, -1), style=0)
        self.VTK_OBJECT_CHOICE_ID  =  wxNewId()
        self.object_choice = wxChoice(self, self.VTK_OBJECT_CHOICE_ID , choices=['vtkDICOMVolumeReader'], size=(-1, -1), style=0)
        self.label_2 = wxStaticText(self, -1, "Examine the", size=(-1, -1), style=0)
        self.sizer_3 = wxBoxSizer(wxHORIZONTAL)
        self.BROWSE_BUTTON_ID  =  wxNewId()
        self.browse_button = wxButton(self, self.BROWSE_BUTTON_ID , "Browse...", size=(-1, -1))
        self.DIRNAME_TEXT_ID  =  wxNewId()
        self.dirname_text = wxTextCtrl(self, self.DIRNAME_TEXT_ID , "", size=(-1, -1), style=0)
        self.label_1 = wxStaticText(self, -1, "DICOM Directory", size=(-1, -1), style=0)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: __set_properties
        self.SetTitle("vtk_dicom_rdr configuration")
        self.object_choice.SetSelection(0)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: __do_layout
        self.sizer_3.Add(self.label_1, 0, wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
        self.sizer_3.Add(self.dirname_text, 1, wxALIGN_CENTER_VERTICAL, 0)
        self.sizer_3.Add(self.browse_button, 0, wxALIGN_CENTER_VERTICAL, 0)
        self.sizer_1.Add(self.sizer_3, 1, wxBOTTOM|wxRIGHT|wxEXPAND|wxTOP|wxLEFT, 5)
        self.sizer_4.Add(self.label_2, 0, wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
        self.sizer_4.Add(self.object_choice, 0, wxALIGN_CENTER_VERTICAL, 0)
        self.sizer_4.Add(self.label_3, 0, wxRIGHT|wxLEFT|wxALIGN_CENTER_VERTICAL, 2)
        self.sizer_4.Add(self.pipeline_button, 0, wxALIGN_CENTER_VERTICAL, 0)
        self.sizer_1.Add(self.sizer_4, 1, wxBOTTOM|wxRIGHT|wxTOP|wxLEFT, 5)
        self.sizer_2.Add(self.cancel_button, 0, wxBOTTOM|wxRIGHT|wxTOP|wxLEFT, 2)
        self.sizer_2.Add(self.sync_button, 0, wxBOTTOM|wxRIGHT|wxTOP|wxLEFT, 2)
        self.sizer_2.Add(self.apply_button, 0, wxBOTTOM|wxRIGHT|wxTOP|wxLEFT, 2)
        self.sizer_2.Add(self.execute_button, 0, wxBOTTOM|wxRIGHT|wxTOP|wxLEFT, 2)
        self.sizer_2.Add(self.ok_button, 0, wxBOTTOM|wxRIGHT|wxTOP|wxLEFT, 2)
        self.sizer_1.Add(self.sizer_2, 1, wxBOTTOM|wxRIGHT|wxTOP|wxLEFT, 5)
        self.SetAutoLayout(1)
        self.SetSizer(self.sizer_1)
        self.sizer_1.Fit(self)
        # end wxGlade

# end of class vtk_dicom_rdr_view_frame


