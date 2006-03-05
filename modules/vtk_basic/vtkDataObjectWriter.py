# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkDataObjectWriter(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkDataObjectWriter(), 'Writing vtkDataObject.',
            ('vtkDataObject',), (),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)