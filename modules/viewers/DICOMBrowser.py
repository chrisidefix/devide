# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

# Hello there person reading this source!
# At the moment, I'm trying to get a fully-functioning DICOM browser
# out the door as fast as possible.  As soon as the first version is
# out there and my one user can start giving feedback, the following
# major changes are planned:
# * refactoring of the code, specifically to get the dicom slice
#   viewer out into a separate class for re-use in the rest of DeVIDE,
#   for example by the light-table thingy I'm planning.  See issue 38.
# * caching of DICOM searches: a scan of a set of directories will
#   create an sqlite file with all scanned information.  Name of sql
#   file will be stored in config, so that restarts will be REALLY
#   quick.  One will be able to scan (recreate whole cache file) or
#   a quick re-scan (only add new files that have appeared, remove 
#   files that have disappeared).  See issue 39.

import DICOMBrowserFrame
reload(DICOMBrowserFrame)
import gdcm
from module_kits.misc_kit import misc_utils
from module_base import ModuleBase
from module_mixins import IntrospectModuleMixin
import module_utils
import os
import sys
import traceback
import vtk
import vtkgdcm
import wx

class Study:
    def __init__(self):
        self.patient_name = None
        self.patient_id = None
        self.uid = None
        self.description = None
        self.date = None
        # maps from series_uid to Series instance
        self.series_dict = {}
        # total number of slices in complete study
        self.slices = 0

# create list of attributes for serialisation functions
s = Study()
STUDY_ATTRS = [i for i in dir(s) 
                if not i.startswith('__') and 
                i not in ['uid', 'series_dict']] 


class Series:
    def __init__(self):
        self.uid = None
        self.description = None
        self.modality = None
        self.filenames = []
        # number of slices can deviate from number of filenames due to
        # multi-frame DICOM files
        self.slices = 0
        self.rows = 0
        self.columns = 0

# create list of attributes for serialisation functions
s = Series()
SERIES_ATTRS = [i for i in dir(s) 
                if not i.startswith('__') and
                i not in ['uid']] 


class DICOMBrowser(IntrospectModuleMixin, ModuleBase):
    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._view_frame = module_utils.instantiate_module_view_frame(
            self, self._module_manager, 
            DICOMBrowserFrame.DICOMBrowserFrame)
        # change the title to something more spectacular
        # default is DICOMBrowser View
        self._view_frame.SetTitle('DeVIDE DICOMBrowser')

        self._image_viewer = None
        self._setup_image_viewer()

        # map from study_uid to Study instances
        self._study_dict = {}
        # map from studies listctrl itemdata to study uid
        self._item_data_to_study_uid = {}
        # currently selected study_uid
        self._selected_study_uid = None

        self._item_data_to_series_uid = {}
        self._selected_series_uid = None

        # store name of currently previewed filename, so we don't
        # reload unnecessarily.
        self._current_filename = None

        self._bind_events()


        self._config.dicom_search_paths = []
        self._config.lock_pz = False
        self._config.lock_wl = False
        self._config.s_study_dict = {}

        self.sync_module_logic_with_config()
        self.sync_module_view_with_logic()

        self.view()
        # all modules should toggle this once they have shown their
        # stuff.
        self.view_initialised = True

        if os.name == 'posix':
            # bug with GTK where the image window appears bunched up
            # in the top-left corner.  By setting the default view
            # (again), it's worked around
            self._view_frame.set_default_view()

    def close(self):
        
        # with this complicated de-init, we make sure that VTK is 
        # properly taken care of
        self._image_viewer.GetRenderer().RemoveAllViewProps()
        self._image_viewer.SetupInteractor(None)
        self._image_viewer.SetRenderer(None)
        # this finalize makes sure we don't get any strange X
        # errors when we kill the module.
        self._image_viewer.GetRenderWindow().Finalize()
        self._image_viewer.SetRenderWindow(None)
        del self._image_viewer
        # done with VTK de-init

        self._view_frame.close()
        self._view_frame = None
        IntrospectModuleMixin.close(self)

    def get_input_descriptions(self):
        return ()

    def get_output_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        pass

    def get_output(self, idx):
        pass

    def execute_module(self):
        pass

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def config_to_view(self):
        # show DICOM search paths in interface
        tc = self._view_frame.dirs_pane.dirs_files_tc
        tc.SetValue(self._helper_dicom_search_paths_to_string(
            self._config.dicom_search_paths))

        # show value of pz and wl locks
        ip = self._view_frame.image_pane
        ip.lock_pz_cb.SetValue(self._config.lock_pz)
        ip.lock_wl_cb.SetValue(self._config.lock_wl)

        # now load the cached study_dict (if available)
        self._study_dict = self._deserialise_study_dict(
                self._config.s_study_dict)
        self._fill_studies_listctrl()

    def view_to_config(self):
        # self._config is maintained in real-time
        pass

    def view(self):
        self._view_frame.Show()
        self._view_frame.Raise()

        # because we have an RWI involved, we have to do this
        # SafeYield, so that the window does actually appear before we
        # call the render.  If we don't do this, we get an initial
        # empty renderwindow.
        wx.SafeYield()
        self._view_frame.render_image()

    def _bind_events(self):
        vf = self._view_frame
        vf.Bind(wx.EVT_MENU, self._handler_next_image,
                id = vf.id_next_image)
        vf.Bind(wx.EVT_MENU, self._handler_prev_image,
                id = vf.id_prev_image)

        # we unbind the existing mousewheel handler so it doesn't
        # interfere
        self._view_frame.image_pane.rwi.Unbind(wx.EVT_MOUSEWHEEL)
        self._view_frame.image_pane.rwi.Bind(
                wx.EVT_MOUSEWHEEL, self._handler_mousewheel)

        fp = self._view_frame.dirs_pane

        fp.ad_button.Bind(wx.EVT_BUTTON,
                self._handler_ad_button)

        fp.af_button.Bind(wx.EVT_BUTTON,
                self._handler_af_button)

        fp.scan_button.Bind(wx.EVT_BUTTON,
                self._handler_scan_button)
        
        lc = self._view_frame.studies_lc
        lc.Bind(wx.EVT_LIST_ITEM_SELECTED,
                self._handler_study_selected)

        lc = self._view_frame.series_lc
        lc.Bind(wx.EVT_LIST_ITEM_SELECTED,
                self._handler_series_selected)
        # with this one, we'll catch drag events
        lc.Bind(wx.EVT_MOTION, self._handler_series_motion)

        lc = self._view_frame.files_lc
        # we use this event instead of focused, as group / multi
        # selections (click, then shift click 5 items down) would fire
        # selected events for ALL involved items.  With FOCUSED, only
        # the item actually clicked on, or keyboarded to, gets the
        # event.
        lc.Bind(wx.EVT_LIST_ITEM_FOCUSED,
                self._handler_file_selected)
    
        # catch drag events (so user can drag and drop selected files)
        lc.Bind(wx.EVT_MOTION, self._handler_files_motion)

        # the IPP sort button in the files pane
        ipp_sort_button = self._view_frame.files_pane.ipp_sort_button
        ipp_sort_button.Bind(wx.EVT_BUTTON, self._handler_ipp_sort)

        # keep track of the image viewer controls
        ip = self._view_frame.image_pane
        ip.lock_pz_cb.Bind(wx.EVT_CHECKBOX,
                self._handler_lock_pz_cb)
        ip.lock_wl_cb.Bind(wx.EVT_CHECKBOX,
                self._handler_lock_wl_cb)
        ip.reset_b.Bind(wx.EVT_BUTTON,
                self._handler_image_reset_b)

    def _helper_files_to_files_listctrl(self, filenames):
        lc = self._view_frame.files_lc
        lc.DeleteAllItems()

        self._item_data_to_file = {}

        for filename in filenames:
            idx = lc.InsertStringItem(sys.maxint, filename)
            lc.SetItemData(idx, idx)
            self._item_data_to_file[idx] = filename

    def _fill_files_listctrl(self):
        # get out current Study instance
        study = self._study_dict[self._selected_study_uid]
        # then the series_dict belonging to that Study
        series_dict = study.series_dict
        # and finally the specific series instance
        series = series_dict[self._selected_series_uid]

        # finally copy the filenames to the listctrl
        self._helper_files_to_files_listctrl(series.filenames)

        lc = self._view_frame.files_lc 
        # select the first file
        if lc.GetItemCount() > 0:
            lc.Select(0)
            # in this case we have to focus as well, as that's the
            # event that it's sensitive to.
            lc.Focus(0)


    def _fill_series_listctrl(self):
        # get out current Study instance
        study = self._study_dict[self._selected_study_uid]
        # then the series_dict belonging to that Study
        series_dict = study.series_dict

        # clear the ListCtrl
        lc = self._view_frame.series_lc
        lc.DeleteAllItems()
        # shortcut to the columns class
        sc = DICOMBrowserFrame.SeriesColumns

        # we're going to need this for the column sorting
        item_data_map = {}
        self._item_data_to_series_uid = {}

        for series_uid, series in series_dict.items():
            idx = lc.InsertStringItem(sys.maxint, series.description)
            lc.SetStringItem(idx, sc.modality, series.modality)
            lc.SetStringItem(idx, sc.num_images, str(series.slices))
            rc_string = '%d x %d' % (series.columns, series.rows)
            lc.SetStringItem(idx, sc.row_col, rc_string)
            
            # also for the column sorting
            lc.SetItemData(idx, idx)

            item_data_map[idx] = (
                series.description,
                series.modality,
                series.slices,
                rc_string)

            self._item_data_to_series_uid[idx] = series.uid

        lc.itemDataMap = item_data_map

        # select the first series
        if lc.GetItemCount() > 0:
            lc.SetItemState(0, wx.LIST_STATE_SELECTED,
                    wx.LIST_STATE_SELECTED)

    def _fill_studies_listctrl(self):
        """Given a study dictionary, fill out the complete studies
        ListCtrl.

        This will also select the first study, triggering that event
        handler and consequently filling the series control and the
        images control for the first selected series.
        """

        lc = self._view_frame.studies_lc
        # clear the thing out
        lc.DeleteAllItems()

        sc = DICOMBrowserFrame.StudyColumns

        # this is for the columnsorter
        item_data_map = {}
        # this is for figuring out which study is selected in the
        # event handler
        self.item_data_to_study_id = {}
        for study_uid, study in self._study_dict.items():
            # clean way of mapping from item to column?
            idx = lc.InsertStringItem(sys.maxint, study.patient_name)
            lc.SetStringItem(idx, sc.patient_id, study.patient_id)
            lc.SetStringItem(idx, sc.description, study.description)
            lc.SetStringItem(idx, sc.date, study.date)
            lc.SetStringItem(idx, sc.num_images, str(study.slices))
            lc.SetStringItem(
                    idx, sc.num_series, str(len(study.series_dict)))
          
            # we set the itemdata to the current index (this will
            # change with sorting, of course)
            lc.SetItemData(idx, idx) 

            # for sorting we build up this item_data_map with the same
            # hash as key, and the all values occurring in the columns
            # as sortable values
            item_data_map[idx] = (
                    study.patient_name,
                    study.patient_id,
                    study.description,
                    study.date,
                    study.slices,
                    len(study.series_dict))

            self._item_data_to_study_uid[idx] = study.uid

        # assign the datamap to the ColumnSorterMixin
        lc.itemDataMap = item_data_map
        
        if lc.GetItemCount() > 0:
            lc.SetItemState(0, wx.LIST_STATE_SELECTED,
                    wx.LIST_STATE_SELECTED)

        else:
            # this means the study LC is empty, i.e. nothing was
            # found.  In this case, we have to empty the other series
            # and file LCs as well.
            self._view_frame.series_lc.DeleteAllItems()
            self._view_frame.files_lc.DeleteAllItems()

        #lc.auto_size_columns()

    def _handler_ad_button(self, event):

        dlg = wx.DirDialog(self._view_frame, 
            "Choose a directory to add:",
                          style=wx.DD_DEFAULT_STYLE
                           | wx.DD_DIR_MUST_EXIST
                           )

        if dlg.ShowModal() == wx.ID_OK:
            p = dlg.GetPath()
            tc = self._view_frame.dirs_pane.dirs_files_tc
            v = tc.GetValue()
            nv = self._helper_dicom_search_paths_to_string(
                    [v, p])
            tc.SetValue(nv)

        dlg.Destroy()

    def _handler_af_button(self, event):

        dlg = wx.FileDialog(
                self._view_frame, message="Choose files to add:",
                defaultDir="", 
                defaultFile="",
                wildcard="All files (*.*)|*.*",
                style=wx.OPEN | wx.MULTIPLE
                )

        if dlg.ShowModal() == wx.ID_OK:
            tc = self._view_frame.dirs_pane.dirs_files_tc
            v = tc.GetValue()
            nv = self._helper_dicom_search_paths_to_string(
                    [v] + [str(p) for p in dlg.GetPaths()])

            tc.SetValue(nv)


        dlg.Destroy()

    def _handler_file_selected(self, event):
        # this handler gets called one more time AFTER we've destroyed
        # the DICOMBrowserViewFrame, so we have to check.
        if not self._view_frame:
            return

        lc = self._view_frame.files_lc
        idx = lc.GetItemData(event.m_itemIndex)
        filename = self._item_data_to_file[idx]

        if filename == self._current_filename:
            # we're already viewing this filename, don't try to load
            # again.
            return

        # first make sure the image_viewer has a dummy input, so that
        # any previously connected reader can be deallocated first
        self._set_image_viewer_dummy_input()

        # unlike the DICOMReader, we allow the vtkGDCMImageReader to
        # do its y-flipping here.
        r = vtkgdcm.vtkGDCMImageReader()
        r.SetFileName(filename)

        try:
            r.Update()
        except RuntimeWarning, e:
            # reader generates warning of overlay information can't be
            # read.  We should change the VTK exception support to
            # just output some text with a warning and not raise an
            # exception.
            traceback.print_exc()
            # with trackback.format_exc() you can send this to the log
            # window.
        except RuntimeError, e:
            self._module_manager.log_error(
                    'Could not read %s:\n%s.\nSuggest re-Scan.' %
                    (os.path.basename(filename), str(e)))
            return

        self._update_image(r)
        self._update_meta_data_pane(r)

        self._current_filename = filename

    def _handler_ipp_sort(self, event):
        # get out current Study instance
        study = self._study_dict[self._selected_study_uid]
        # then the series_dict belonging to that Study
        series_dict = study.series_dict
        # and finally the specific series instance
        series = series_dict[self._selected_series_uid]

        # have to  cast to normal strings (from unicode)
        filenames = [str(i) for i in series.filenames]

        sorter = gdcm.IPPSorter()
        ret = sorter.Sort(filenames)

        if not ret:
            self._module_manager.log_error(
                    'Could not sort DICOM filenames. ' + 
                    'It could be that this is an invalid collection.')
            return

        selected_idx = -1
        del series.filenames[:]
        for idx,fn in enumerate(sorter.GetFilenames()):
            series.filenames.append(fn)
            if idx >= 0 and fn == self._current_filename:
                selected_idx = idx

        lc = self._view_frame.files_lc
        

        # now overwrite the listctrl with these sorted filenames
        self._helper_files_to_files_listctrl(series.filenames)
        
        # select the file that was selected prior to the sort
        if selected_idx >= 0:
            lc.Select(selected_idx)
            lc.Focus(selected_idx)



    def _handler_mousewheel(self, event):
        # event.GetWheelRotation() is + or - 120 depending on
        # direction of turning.
        if event.ControlDown():
            delta = 10
        else:
            delta = 1
         
        if event.GetWheelRotation() > 0:
            self._helper_prev_image(delta)
        else:
            self._helper_next_image(delta)

    def _handler_next_image(self, event):
        self._helper_next_image()

    def _handler_prev_image(self, event):
        self._helper_prev_image()

    def _helper_next_image(self, delta=1):
        """Go to next image.

        We could move this to the display code, it only needs to know
        about widgets.
        """

        # first see if we're previewing a multi-slice DICOM file
        next_file = True
        range = [0,0]
        self._image_viewer.GetSliceRange(range)
        if range[1] - range[0] != 0:
            cur_slice = self._image_viewer.GetSlice()
            if cur_slice <= range[1] - delta:
                new_slice = cur_slice + delta
                self._image_viewer.SetSlice(new_slice)
                self._image_viewer.ul_text_actor.frnum = new_slice
                self._update_image_ul_text()

                next_file = False

        if next_file:
            lc = self._view_frame.files_lc
            nidx = lc.GetFocusedItem() + delta
            if nidx >= lc.GetItemCount():
                nidx = lc.GetItemCount() - 1

            lc.Focus(nidx)

    def _helper_prev_image(self, delta=1):
        """Move to previous image.

        We could move this to the display code, it only needs to know
        about widgets.
        """
       
        # first see if we're previewing a multi-slice DICOM file
        prev_file = True
        range = [0,0]
        self._image_viewer.GetSliceRange(range)
        if range[1] - range[0] != 0:
            cur_slice = self._image_viewer.GetSlice()
            if cur_slice >= range[0] + delta:
                new_slice = cur_slice - delta
                self._image_viewer.SetSlice(new_slice)
                self._image_viewer.ul_text_actor.frnum = new_slice
                self._update_image_ul_text()

                prev_file = False

        if prev_file:
            lc = self._view_frame.files_lc
            nidx = lc.GetFocusedItem() - delta
            if nidx < 0:
                nidx = 0

            lc.Focus(nidx)

    def _read_all_tags(self, filename):
        r = gdcm.Reader(filename)
        r.Read()
        f = r.GetFile()
        ds = file.GetDataSet()
        pds = gdcm.PythonDataSet(ds)
        sf = gdcm.StringFilter()
        pds.Start() # Make iterator go at begining
        dic={}
        sf.SetFile(f) # extremely important
        while(not pds.IsAtEnd() ):
                res = sf.ToStringPair( pds.GetCurrent().GetTag() )
                dic[res[0]] = res[1]
                pds.Next()

        return dic


    def _update_image_ul_text(self):
        """Updates upper left text actor according to relevant
        instance variables.
        """

        ul = self._image_viewer.ul_text_actor
        imsize_str = 'Image Size: %d x %d' % (ul.imsize) 
        imnum_str = 'Image # %s' % (ul.imnum,)
        frnum_str = 'Frame # %d' % (ul.frnum,)
        ul.SetInput('%s\n%s\n%s' % (
            imsize_str, imnum_str, frnum_str))

    def _update_image(self, gdcm_reader):
        """Given a vtkGDCMImageReader instance that has read the given
        file, update the image viewer.
        """

        r = gdcm_reader

        self._image_viewer.SetInput(r.GetOutput())
        #if r.GetNumberOfOverlays():
        #    self._image_viewer.AddInput(r.GetOverlay(0))

        # now make the nice text overlay thingies!

        # DirectionCosines: first two columns are X and Y in the LPH
        # coordinate system
        dc = r.GetDirectionCosines()

        x_cosine = \
                dc.GetElement(0,0), dc.GetElement(1,0), dc.GetElement(2,0)

        lph = misc_utils.major_axis_from_iop_cosine(x_cosine)
        if lph:
            self._image_viewer.xl_text_actor.SetInput(lph[0])
            self._image_viewer.xr_text_actor.SetInput(lph[1])
        else:
            self._image_viewer.xl_text_actor.SetInput('X')
            self._image_viewer.xr_text_actor.SetInput('X')

        y_cosine = \
                dc.GetElement(0,1), dc.GetElement(1,1), dc.GetElement(2,1)
        lph = misc_utils.major_axis_from_iop_cosine(y_cosine)

        if lph:
            if r.GetFileLowerLeft():
                # no swap
                b = lph[0]
                t = lph[1]
            else:
                # we have to swap these around because VTK has the
                # convention of image origin at the upper left and GDCM
                # dutifully swaps the images when loading to follow this
                # convention.  Direction cosines (IOP) is not swapped, so
                # we have to compensate here.
                b = lph[1]
                t = lph[0]

            self._image_viewer.yb_text_actor.SetInput(b)
            self._image_viewer.yt_text_actor.SetInput(t)

        else:
            self._image_viewer.yb_text_actor.SetInput('X')
            self._image_viewer.yt_text_actor.SetInput('X')

        mip = r.GetMedicalImageProperties()
        
        d = r.GetOutput().GetDimensions()

        ul = self._image_viewer.ul_text_actor
        ul.imsize = (d[0], d[1])
        ul.imnum = mip.GetImageNumber() # string
        ul.frnum = self._image_viewer.GetSlice()
        self._update_image_ul_text()

        ur = self._image_viewer.ur_text_actor
        ur.SetInput('%s\n%s\n%s\n%s' % (
            mip.GetPatientName(),
            mip.GetPatientID(),
            mip.GetStudyDescription(),
            mip.GetSeriesDescription()))

        br = self._image_viewer.br_text_actor
        br.SetInput('DeVIDE\nTU Delft')

        # we have a new image in the image_viewer, so we have to reset
        # the camera so that the image is visible.
        if not self._config.lock_pz:
            self._reset_image_pz()

        # also reset window level
        if not self._config.lock_wl:
            self._reset_image_wl()

        self._image_viewer.Render()



    def _update_meta_data_pane(self, gdcm_reader):
        """Given a vtkGDCMImageReader instance that was used to read a
        file, update the meta-data display.
        """

        # update image meta-data #####
        r = gdcm_reader
        mip = r.GetMedicalImageProperties()

        r_attr_l = [
                'DataOrigin',
                'DataSpacing'
        ]

        import module_kits.vtk_kit
        mip_attr_l = \
            module_kits.vtk_kit.constants.medical_image_properties_keywords
                


        item_data_map = {}
        lc = self._view_frame.meta_lc

        # only start over if we have to to avoid flickering and
        # resetting of scroll bars.
        if lc.GetItemCount() != (len(r_attr_l) + len(mip_attr_l)):
            lc.DeleteAllItems() 
            reset_lc = True
        else:
            reset_lc = False

        def helper_av_in_lc(a, v, idx):
            if reset_lc:
                # in the case of a reset (i.e. we have to build up the
                # listctrl from scratch), the idx param is ignored as
                # we overwrite it with our own here
                idx = lc.InsertStringItem(sys.maxint, a)
            else:
                # not a reset, so we use the given idx
                lc.SetStringItem(idx, 0, a)

            lc.SetStringItem(idx, 1, v)
            lc.SetItemData(idx, idx)
            item_data_map[idx] = (a, v)

        idx = 0
        for a in r_attr_l:
            v = str(getattr(r, 'Get%s' % (a,))())
            helper_av_in_lc(a, v, idx)
            idx = idx + 1

        for a in mip_attr_l:
            v = str(getattr(mip, 'Get%s' % (a,))())
            helper_av_in_lc(a, v, idx)
            idx = idx + 1



        # so that sorting (kinda) works
        lc.itemDataMap = item_data_map

    def _handler_image_reset_b(self, event):
        self._reset_image_pz()
        self._reset_image_wl()
        self._image_viewer.Render()
        
    def _handler_lock_pz_cb(self, event):
        cb = self._view_frame.image_pane.lock_pz_cb 
        self._config.lock_pz = cb.GetValue()

        # when the user unlocks pan/zoom, reset it for the current
        # image
        if not self._config.lock_pz:
            self._reset_image_pz()
            self._image_viewer.Render()
      

    def _handler_lock_wl_cb(self, event):
        cb = self._view_frame.image_pane.lock_wl_cb 
        self._config.lock_wl = cb.GetValue()
        
        # when the user unlocks window / level, reset it for the
        # current image
        if not self._config.lock_wl:
            self._reset_image_wl()
            self._image_viewer.Render()

    def _handler_scan_button(self, event):
        tc = self._view_frame.dirs_pane.dirs_files_tc

        # helper function discards empty strings and strips the rest
        paths = self._config.dicom_search_paths = \
                self._helper_dicom_search_paths_to_list(tc.GetValue())

        # let's put it back in the interface too
        tc.SetValue(self._helper_dicom_search_paths_to_string(paths))
        
        try:
            self._study_dict = self._scan(paths)
        except Exception, e:
            # also print the exception
            traceback.print_exc()
            # i don't want to use log_error_with_exception, because it
            # uses a non-standard dialogue box that pops up over the
            # main devide window instead of the module view.
            self._module_manager.log_error(
                    'Error scanning DICOM files: %s' % (str(e)))

        # serialise study_dict into config
        self._config.s_study_dict = self._serialise_study_dict(
                self._study_dict)

        # do this in anycase...
        self._fill_studies_listctrl()

    def _handler_files_motion(self, event):
        """Handler for when user drags a file selection somewhere.
        """

        if not event.Dragging():
            event.Skip()
            return

        lc = self._view_frame.files_lc

        selected_idxs = []
        s = lc.GetFirstSelected()
        while s != -1:
            selected_idxs.append(s)
            s = lc.GetNextSelected(s)

        if len(selected_idxs) > 0:
            data_object = wx.FileDataObject()
            for idx in selected_idxs:
                data_object.AddFile(self._item_data_to_file[idx])

            drop_source = wx.DropSource(lc)
            drop_source.SetData(data_object)
            drop_source.DoDragDrop(False)

    def _handler_series_motion(self, event):
        if not event.Dragging():
            event.Skip()
            return

        # get out current Study instance
        try:
            study = self._study_dict[self._selected_study_uid]
        except KeyError:
            return

        # then the series_dict belonging to that Study
        series_dict = study.series_dict
        # and finally the specific series instance
        # series.filenames is a list of the filenames
        try:
            series = series_dict[self._selected_series_uid]
        except KeyError:
            return

        # according to the documentation, we can only write to this
        # object on Windows and GTK2.  Hrrmmpph.
        # FIXME.  Will have to think up an alternative solution on
        # OS-X
        data_object = wx.FileDataObject()
        for f in series.filenames:
            data_object.AddFile(f)

        drop_source = wx.DropSource(self._view_frame.series_lc)
        drop_source.SetData(data_object)
        # False means that files will be copied, NOT moved
        drop_source.DoDragDrop(False)

    def _handler_series_selected(self, event):
        lc = self._view_frame.series_lc
        idx = lc.GetItemData(event.m_itemIndex)
        series_uid = self._item_data_to_series_uid[idx]
        self._selected_series_uid = series_uid

        print 'series_uid', series_uid

        self._fill_files_listctrl()

    def _handler_study_selected(self, event):
        # we get the ItemData from the currently selected ListCtrl
        # item
        lc = self._view_frame.studies_lc
        idx = lc.GetItemData(event.m_itemIndex)
        # and then use this to find the current study_uid
        study_uid = self._item_data_to_study_uid[idx]
        self._selected_study_uid = study_uid

        print 'study uid', study_uid

        self._fill_series_listctrl()

    def _helper_dicom_search_paths_to_string(
            self, dicom_search_paths):
        """Given a list of search paths, append them into a semicolon
        delimited string.
        """
        s = [i.strip() for i in dicom_search_paths]
        s2 = [i for i in s if len(i) > 0]
        return ' ; '.join(s2)

    def _helper_dicom_search_paths_to_list(
            self, dicom_search_paths):
        """Given a semicolon-delimited string, break into list.
        """

        s = [str(i.strip()) for i in dicom_search_paths.split(';')]
        return [i for i in s if len(i) > 0]

    def _helper_recursive_glob(self, paths):
        """Given a combined list of files and directories, return a
        combined list of sorted and unique fully-qualified filenames,
        consisting of the supplied filenames and a recursive search
        through all supplied directories.
        """

        # we'll use this to keep all filenames unique 
        files_dict = {}
        d = gdcm.Directory()

        for path in paths:
            if os.path.isdir(path):
                # we have to cast path to str (it's usually unicode)
                # else the gdcm wrappers error on "bad number of
                # arguments to overloaded function"
                d.Load(str(path), True)
                # fromkeys creates a new dictionary with GetFilenames
                # as keys; then update merges this dictionary with the
                # existing files_dict
                normed = [os.path.normpath(i) for i in d.GetFilenames()]
                files_dict.update(dict.fromkeys(normed, 1))

            elif os.path.isfile(path):
                files_dict[os.path.normpath(path)] = 1


        # now sort everything
        filenames = files_dict.keys()
        filenames.sort()

        return filenames

    def _reset_image_pz(self):
        """Reset the pan/zoom of the current image.
        """

        ren = self._image_viewer.GetRenderer()
        ren.ResetCamera()

    def _reset_image_wl(self):
        """Reset the window/level of the current image.

        This assumes that the image has already been read and that it
        has a valid scalar range.
        """
        
        iv = self._image_viewer
        inp = iv.GetInput()
        if inp:
            r = inp.GetScalarRange()
            iv.SetColorWindow(r[1] - r[0])
            iv.SetColorLevel(0.5 * (r[1] + r[0]))

    def _scan(self, paths):
        """Given a list combining filenames and directories, search
        recursively to find all valid DICOM files.  Build
        dictionaries.
        """

        # UIDs are unique for their domains.  Patient ID for example
        # is not unique.
        # Instance UID (0008,0018)
        # Patient ID (0010,0020)
        # Study UID (0020,000D) - data with common procedural context
        # Study description (0008,1030)
        # Series UID (0020,000E)

        # see http://public.kitware.com/pipermail/igstk-developers/
        # 2006-March/000901.html for explanation w.r.t. number of
        # frames; for now we are going to assume that this refers to
        # the number of included slices (as is the case for the
        # Toshiba 320 slice for example)

        tag_to_symbol = {
                (0x0008, 0x0018) : 'instance_uid',
                (0x0010, 0x0010) : 'patient_name',
                (0x0010, 0x0020) : 'patient_id',
                (0x0020, 0x000d) : 'study_uid',
                (0x0008, 0x1030) : 'study_description',
                (0x0008, 0x0020) : 'study_date',
                (0x0020, 0x000e) : 'series_uid',
                (0x0008, 0x103e) : 'series_description',
                (0x0008, 0x0060) : 'modality', # fixed per series
                (0x0028, 0x0008) : 'number_of_frames',
                (0x0028, 0x0010) : 'rows',
                (0x0028, 0x0011) : 'columns'
                }

        # find list of unique and sorted filenames
        filenames = self._helper_recursive_glob(paths)
        
        s = gdcm.Scanner()
        # add the tags we want to the scanner
        for tag_tuple in tag_to_symbol:
            tag = gdcm.Tag(*tag_tuple)
            s.AddTag(tag)

        # maps from study_uid to instance of Study
        study_dict = {}

        # we're going to break the filenames up into 10 blocks and
        # scan each block separately in order to be able to give
        # proper feedback to the user, and also to give the user the
        # opportunity to interrupt the scan
        num_files = len(filenames)

        # no filenames, we return an empty dict.
        if num_files == 0:
            return study_dict

        num_files_per_block = 100 
        num_blocks = num_files / num_files_per_block 
        if num_blocks == 0:
            num_blocks = 1

        blocklen = num_files / num_blocks
        blockmod = num_files % num_blocks

        block_lens = [blocklen] * num_blocks
        if blockmod > 0:
            block_lens += [blockmod]

        file_idx = 0 
        progress = 0.0 

        # setup progress dialog
        dlg = wx.ProgressDialog("DICOMBrowser",
                                "Scanning DICOM data",
                                maximum = 100,
                                parent=self._view_frame,
                                style = wx.PD_CAN_ABORT
                                | wx.PD_APP_MODAL
                                | wx.PD_ELAPSED_TIME
                                | wx.PD_AUTO_HIDE
                                #| wx.PD_ESTIMATED_TIME
                                | wx.PD_REMAINING_TIME
                                )
        keep_going = True
        error_occurred = False

        # and now the processing loop can start
        for block_len in block_lens:
            # scan the current block of files
            try:
                self._helper_scan_block(
                        s, filenames[file_idx:file_idx + block_len],
                        tag_to_symbol, study_dict)
            except Exception:
                # error during scan, we have to kill the dialog and
                # then re-raise the error
                dlg.Destroy()
                raise


            # update file_idx for the next block
            file_idx += block_len
            # update progress counter
            progress = int(100 * file_idx / float(num_files))
            # and tell the progress dialog about our progress
            # by definition, progress will be 100 at the end: if you
            # add all blocklens together, you have to get 1
            (keep_going, skip) = dlg.Update(progress)

            if not keep_going:
                # user has clicked cancel so we zero the dictionary
                study_dict = {}
                # and stop the for loop
                break

        # dialog needs to be taken care of
        dlg.Destroy()

        # return all the scanned data
        return study_dict

    def _helper_scan_block(
            self, s, filenames, tag_to_symbol, study_dict):
        """Scan list of filenames, fill study_dict.  Used by _scan()
        to scan list of filenames in blocks.
        """

        # d.GetFilenames simply returns a tuple with all
        # fully-qualified filenames that it finds.
        ret = s.Scan(filenames)
        if not ret:
            print "scanner failed"
            return

        # s now contains a Mapping (std::map) from filenames to stuff
        # calling s.GetMapping(full filename) returns a TagToValue
        # which we convert for our own use with a PythonTagToValue
        #pttv = gdcm.PythonTagToValue(mapping)

        # what i want:
        # a list of studies (indexed on study id): each study object
        # contains metadata we want to list per study, plus a list of
        # series belonging to that study.

        for f in filenames:
            mapping = s.GetMapping(f)

            # with this we can iterate through all tags for this file
            # let's store them all...
            file_tags = {}
            pttv = gdcm.PythonTagToValue(mapping)
            pttv.Start()
            while not pttv.IsAtEnd():
                tag = pttv.GetCurrentTag() # gdcm::Tag
                val = pttv.GetCurrentValue() # string

                symbol = tag_to_symbol[(tag.GetGroup(), tag.GetElement())]
                file_tags[symbol] = val

                pttv.Next()

            # take information from file_tags, stuff into all other
            # structures...

            # we need at least study and series UIDs to continue
            if not ('study_uid' in file_tags and \
                    'series_uid' in file_tags):
                continue
            
            study_uid = file_tags['study_uid']
            series_uid = file_tags['series_uid']
           
            # create a new study if it doesn't exist yet
            try:
                study = study_dict[study_uid]
            except KeyError:
                study = Study()
                study.uid = study_uid

                study.description = file_tags.get(
                        'study_description', '')
                study.date = file_tags.get(
                        'study_date', '')
                study.patient_name = file_tags.get(
                        'patient_name', '')
                study.patient_id = file_tags.get(
                        'patient_id', '')

                study_dict[study_uid] = study

            try:
                series = study.series_dict[series_uid]
            except KeyError:
                series = Series()
                series.uid = series_uid
                # these should be the same over the whole series
                series.description = \
                    file_tags.get('series_description', '')
                series.modality = file_tags.get('modality', '')

                series.rows = int(file_tags.get('rows', 0))
                series.columns = int(file_tags.get('columns', 0))

                study.series_dict[series_uid] = series

            series.filenames.append(f)

            
            try:
                number_of_frames = int(file_tags['number_of_frames'])
            except KeyError:
                # means number_of_frames wasn't found
                number_of_frames = 1

            series.slices = series.slices + number_of_frames
            study.slices = study.slices + number_of_frames

    def _deserialise_study_dict(self, s_study_dict):
        """Given a serialised study_dict, as generated by
        _serialise_study_dict, reconstruct a real study_dict and
        return it.
        """

        study_dict = {}

        for study_uid, s_study in s_study_dict.items():
            study = Study()
            for a in STUDY_ATTRS:
                setattr(study, a, s_study[a])

            # explicitly put the uid back
            study.uid = study_uid

            s_series_dict = s_study['s_series_dict']
            for series_uid, s_series in s_series_dict.items():
                series = Series()
                for a in SERIES_ATTRS:
                    setattr(series, a, s_series[a])

                series.uid = series_uid

                study.series_dict[series_uid] = series

            study_dict[study_uid] = study

        return study_dict

    def _serialise_study_dict(self, study_dict):
        """Serialise complete study_dict (including all instances of
        Study and of Series) into a simpler form that can be
        successfully pickled.

        Directly pickling the study_dict, then restoring a network and
        trying to serialise again yields the infamous:
        'Can't pickle X: it's not the same object as X' where X is
        modules.viewers.DICOMBrowser.Study
        """


        s_study_dict = {}

        for study_uid, study in study_dict.items():
            s_study = {}
            for a in STUDY_ATTRS:
                v = getattr(study, a)
                s_study[a] = v


            s_series_dict = {}
            for series_uid, series in study.series_dict.items():
                s_series = {}
                for a in SERIES_ATTRS:
                    v = getattr(series, a)
                    s_series[a] = v

                s_series_dict[series_uid] = s_series

            s_study['s_series_dict'] = s_series_dict
            s_study_dict[study_uid] = s_study

        return s_study_dict

    def _set_image_viewer_dummy_input(self):
        ds = vtk.vtkImageGridSource()
        self._image_viewer.SetInput(ds.GetOutput())


    def _setup_image_viewer(self):
        # FIXME: I'm planning to factor this out into a medical image
        # viewing class, probably in the GDCM_KIT

        # setup VTK viewer with dummy source (else it complains)
        self._image_viewer = vtkgdcm.vtkImageColorViewer()
        self._image_viewer.SetupInteractor(self._view_frame.image_pane.rwi)
        self._set_image_viewer_dummy_input()

        def setup_text_actor(x, y):
            ta = vtk.vtkTextActor()

            c = ta.GetPositionCoordinate()
            c.SetCoordinateSystemToNormalizedDisplay()
            c.SetValue(x,y)

            p = ta.GetTextProperty()
            p.SetFontFamilyToArial()
            p.SetFontSize(14)
            p.SetBold(0)
            p.SetItalic(0)
            p.SetShadow(0)

            return ta

        ren = self._image_viewer.GetRenderer()

        # direction labels left and right #####
        xl = self._image_viewer.xl_text_actor = setup_text_actor(0.01, 0.5)
        ren.AddActor(xl)
        xr = self._image_viewer.xr_text_actor = setup_text_actor(0.99, 0.5)
        xr.GetTextProperty().SetJustificationToRight()
        ren.AddActor(xr)

        # direction labels top and bottom #####
        # y coordinate ~ 0, bottom of normalized display
        yb = self._image_viewer.yb_text_actor = setup_text_actor(
                0.5, 0.01)
        ren.AddActor(yb)

        yt = self._image_viewer.yt_text_actor = setup_text_actor(
                0.5, 0.99)
        yt.GetTextProperty().SetVerticalJustificationToTop()
        ren.AddActor(yt)
                
        # labels upper-left #####
        ul = self._image_viewer.ul_text_actor = \
            setup_text_actor(0.01, 0.99)
        ul.GetTextProperty().SetVerticalJustificationToTop()
        ren.AddActor(ul)

        # labels upper-right #####
        ur = self._image_viewer.ur_text_actor = \
            setup_text_actor(0.99, 0.99)
        ur.GetTextProperty().SetVerticalJustificationToTop()
        ur.GetTextProperty().SetJustificationToRight()
        ren.AddActor(ur)

        # labels bottom-right #####
        br = self._image_viewer.br_text_actor = \
            setup_text_actor(0.99, 0.01)
        br.GetTextProperty().SetVerticalJustificationToBottom()
        br.GetTextProperty().SetJustificationToRight()
        ren.AddActor(br)
       


        

