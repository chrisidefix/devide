# $Id$

import fixitk as itk
import genUtils
from moduleBase import moduleBase
import moduleUtils
import moduleUtilsITK
from moduleMixins import scriptedConfigModuleMixin

# the categories that we belong to
DVM_CATS = 'Insight', 'Morphology'
# specify kits that we are dependent on
DVM_KITS = 'vtk_kit', 'itk_kit'

class watershed(scriptedConfigModuleMixin, moduleBase):

    """Perform watershed segmentation on input.

    Typically, the input will be the gradient magnitude image.  Often, data
    is smoothed with one of the anisotropic diffusion filters and then the
    gradient magnitude image is calculated.  This serves as input to the
    watershed module.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)

        # pre-processing on input image: it will be thresholded
        self._config.threshold = 0.1
        # flood level: this will be the starting level of precipitation
        self._config.level = 0.1

        configList = [
            ('Threshold:', 'threshold', 'base:float', 'text',
             'Pre-processing image threshold (0.0-1.0).'),
            ('Level:', 'level', 'base:float', 'text',
             'Initial precipitation level (0.0-1.0).')]
        
        scriptedConfigModuleMixin.__init__(self, configList)


        # setup the pipeline
        self._watershed = itk.itkWatershedImageFilterF3_New()
        
        moduleUtilsITK.setupITKObjectProgress(
            self, self._watershed, 'itkWatershedImageFilter',
            'Performing watershed')

        self._createWindow(
            {'Module (self)' : self,
             'itkWatershedImageFilter' : self._watershed})

        self.configToLogic()
        self.logicToConfig()
        self.configToView()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)
            
        # remove all bindings
        del self._watershed

    def executeModule(self):
        self._watershed.Update()
        self._moduleManager.setProgress(100, "Watershed complete.")

    def getInputDescriptions(self):
        return ('ITK Image (3D, float)',)

    def setInput(self, idx, inputStream):
        self._watershed.SetInput(inputStream)

    def getOutputDescriptions(self):
        return ('ITK Image (3D, unsigned long)',)

    def getOutput(self, idx):
        return self._watershed.GetOutput()

    def configToLogic(self):
        self._config.threshold = genUtils.clampVariable(
            self._config.threshold, 0.0, 1.0)
        self._watershed.SetThreshold(self._config.threshold)
        
        self._config.level = genUtils.clampVariable(
            self._config.level, 0.0, 1.0)
        self._watershed.SetLevel(self._config.level)

    def logicToConfig(self):
        self._config.threshold = self._watershed.GetThreshold()
        self._config.level = self._watershed.GetLevel()

