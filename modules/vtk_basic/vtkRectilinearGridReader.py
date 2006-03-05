# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkRectilinearGridReader(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkRectilinearGridReader(), 'Reading vtkRectilinearGrid.',
            (), ('vtkRectilinearGrid',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)
