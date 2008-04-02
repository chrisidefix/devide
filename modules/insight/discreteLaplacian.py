# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import itk
import module_kits.itk_kit as itk_kit
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin

class discreteLaplacian(noConfigModuleMixin, moduleBase):
    
    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)


        # setup the pipeline
        if3 = itk.Image[itk.F, 3]
        self._laplacian = itk.LaplacianImageFilter[if3,if3].New()
        
        itk_kit.utils.setupITKObjectProgress(
            self, self._laplacian,
            'itkLaplacianImageFilter',
            'Calculating Laplacian')

        noConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self,
             'itkLaplacianImageFilter' :
             self._laplacian})
            
        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._laplacian

    def execute_module(self):
        self._laplacian.Update()

    def get_input_descriptions(self):
        return ('Image (ITK, 3D, float)',)

    def set_input(self, idx, inputStream):
        self._laplacian.SetInput(inputStream)

    def get_output_descriptions(self):
        return ('Laplacian image (ITK, 3D, float)',)    

    def get_output(self, idx):
        return self._laplacian.GetOutput()

