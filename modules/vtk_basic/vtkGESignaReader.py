# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkGESignaReader(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkGESignaReader(), 'Reading vtkGESigna.',
            (), ('vtkGESigna',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
