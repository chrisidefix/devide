class batchConverter:
    kits = ['vtk_kit', 'wx_kit']
    cats = ['Readers','Writers','Converters']
    keywords = ['batch','convert','read','write','vti','mha','gipl']
    help = """Batch converts image volume files from one type to another.
    Source and target types can be VTK ImageData (.vti), MetaImage (.mha), 
	or Guys Image Processing Lab (.gipl).
    
    All the files in the specified directory matching the given 
    source extension are converted. 
    The user may specify whether source files should be deleted 
    or target files should be automatically overwritten (be careful 
    with these settings!)
    
    (Module by Francois Malan)"""

class cptBrepWRT:
    kits = ['vtk_kit']
    cats = ['Writers']    
    help = """Writes polydata to disc in the format required by the Closest
    Point Transform (CPT) driver software.  Input data is put through
    a triangle filter first, as that is what the CPT requires.

    See the
    <a href="http://www.acm.caltech.edu/~seanm/projects/cpt/cpt.html">CPT
    home page</a> for more information about the algorithm and the
    software.
    """

class DICOMWriter:
    kits = ['vtk_kit', 'gdcm_kit']
    cats = ['Writers', 'Medical', 'DICOM']
    help = """Writes image data to disc as DICOM images.

    This GDCM2-based module writes data to disc as one (multi-frame)
    or more DICOM files.  As input, it requires a special DeVIDE
    datastructure containing the raw data, the medical image
    properties and direction cosines (indicating the orientation of
    the dataset in world / scanner space).  You can create such a
    datastructure by making use of the DVMedicalImageData module.

    """

class ivWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """ivWRT is an Inventor Viewer polygonal data writer devide module.
    """


class metaImageWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes VTK image data or structured points in MetaImage format.
    """

class pngWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes a volume as a series of PNG images.

    Set the file pattern by making use of the file browsing dialog.  Replace
    the increasing index by a %d format specifier.  %3d can be used for
    example, in which case %d will be replaced by an integer zero padded to 3
    digits, i.e. 000, 001, 002 etc.  %d starts from 0.

    Module by Joris van Zwieten.
    """

class MatlabPointsWriter:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes slice3dVWR world-points to an m-file.
    """

class points_writer:
    # BUG: empty kits list screws up dependency checking
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """TBD
    """


class stlWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes STL format data.
    """

class vtiWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes VTK image data or structured points in the VTK XML
    format. The data attribute is compressed.

    This is the preferred way of saving image data in DeVIDE.
    """

class vtkPolyDataWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Module for writing legacy VTK polydata.  vtpWRT should be
    preferred for all VTK-compatible polydata storage.
    """

class vtkStructPtsWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Module for writing legacy VTK structured points data.  vtiWRT
    should be preferred for all VTK-compatible image data storage.
    """

class vtpWRT:
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """Writes VTK PolyData in the VTK XML format.  The data attribute
    is compressed.

    This is the preferred way of saving PolyData in DeVIDE.
    """



