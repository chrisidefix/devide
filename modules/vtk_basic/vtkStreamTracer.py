# class generated by DeVIDE::createDeVIDEModuleFromVTKObject
from module_kits.vtk_kit.mixins import SimpleVTKClassModuleBase
import vtk

class vtkStreamTracer(SimpleVTKClassModuleBase):
    def __init__(self, moduleManager):
        SimpleVTKClassModuleBase.__init__(
            self, moduleManager,
            vtk.vtkStreamTracer(), 'Processing.',
            ('vtkDataSet', 'vtkDataSet'), ('vtkPolyData',),
            replaceDoc=True,
            inputFunctions=None, outputFunctions=None)