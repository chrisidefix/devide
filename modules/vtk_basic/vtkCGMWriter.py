# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkCGMWriter(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkCGMWriter(), 'Writing vtkCGM.',
            ('vtkCGM',), (),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
