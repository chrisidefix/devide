# $Id$

from moduleBase import moduleBase
from moduleMixins import filenameViewModuleMixin
import moduleUtils
import vtk


class vtpRDR(moduleBase, filenameViewModuleMixin):
    def __init__(self, moduleManager):

        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        self._reader = vtk.vtkXMLPolyDataReader()

        # ctor for this specific mixin
        filenameViewModuleMixin.__init__(
            self,
            'Select a filename',
            'VTK Poly Data (*.vtp)|*.vtp|All files (*)|*',
            {'vtkXMLPolyDataReader': self._reader})

        moduleUtils.setupVTKObjectProgress(
            self, self._reader,
            'Reading VTK PolyData')

        self._viewFrame = None

        # set up some defaults
        self._config.filename = ''
        self.sync_module_logic_with_config()
        
    def close(self):
        del self._reader
        filenameViewModuleMixin.close(self)

    def get_input_descriptions(self):
        return ()
    
    def set_input(self, idx, input_stream):
        raise Exception
    
    def get_output_descriptions(self):
        return ('vtkPolyData',)
    
    def get_output(self, idx):
        return self._reader.GetOutput()

    def logic_to_config(self):
        filename = self._reader.GetFileName()
        if filename == None:
            filename = ''

        self._config.filename = filename

    def config_to_logic(self):
        self._reader.SetFileName(self._config.filename)

    def view_to_config(self):
        self._config.filename = self._getViewFrameFilename()

    def config_to_view(self):
        self._setViewFrameFilename(self._config.filename)
    
    def execute_module(self):
        # get the vtkPolyDataReader to try and execute
        if len(self._reader.GetFileName()):
            self._reader.Update()
            
