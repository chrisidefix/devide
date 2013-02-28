# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

class BMPReader:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reads a series of BMP files.

    Set the file pattern by making use of the file browsing dialog.  Replace
    the increasing index by a %d format specifier.  %03d can be used for
    example, in which case %d will be replaced by an integer zero padded to 3
    digits, i.e. 000, 001, 002 etc.  %d counts from the 'First slice' to the
    'Last slice'.

    """

class DICOMReader:
    kits = ['vtk_kit']
    cats = ['Readers', 'Medical', 'DICOM']
    help = """New module for reading DICOM data.

    GDCM-based module for reading DICOM data.  This is newer than
    dicomRDR (which is DCMTK-based) and should be able to read more
    kinds of data.  The interface is deliberately less rich, as the
    DICOMReader is supposed to be used in concert with the
    DICOMBrowser.

    If DICOMReader fails to read your DICOM data, please also try the
    dicomRDR as its code is a few more years more mature than that of
    the more flexible but younger DICOMReader.
    """

class dicomRDR:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Module for reading DICOM data.

    This is older DCMTK-based DICOM reader class.  It used to be the
    default in DeVIDE before the advent of the GDCM-based DICOMReader
    in 8.5.

    Add DICOM files (they may be from multiple series) by using the 'Add'
    button on the view/config window.  You can select multiple files in
    the File dialog by holding shift or control whilst clicking.  You
    can also drag and drop files from a file or DICOM browser either
    onto an existing dicomRDR or directly onto the Graph Editor
    canvas.
    """

class JPEGReader:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reads a series of JPG (JPEG) files.

    Set the file pattern by making use of the file browsing dialog.  Replace
    the increasing index by a %d format specifier.  %03d can be used for
    example, in which case %d will be replaced by an integer zero padded to 3
    digits, i.e. 000, 001, 002 etc.  %d counts from the 'First slice' to the
    'Last slice'.
    """


class metaImageRDR:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reads MetaImage format files.

    MetaImage files have an .mha or .mhd file extension.  .mha files are
    single files containing header and data, whereas .mhd are separate headers
    that refer to a separate raw data file.
    """


class objRDR:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reader for OBJ polydata format.
    """

class plyRDR:	
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reader for the Polygon File Format (Stanford Triangle Format) polydata format.
    """
	
class pngRDR:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reads a series of PNG files.

    Set the file pattern by making use of the file browsing dialog.  Replace
    the increasing index by a %d format specifier.  %03d can be used for
    example, in which case %d will be replaced by an integer zero padded to 3
    digits, i.e. 000, 001, 002 etc.  %d counts from the 'First slice' to the
    'Last slice'.
    """

class points_reader:
    # BUG: empty kits list screws up dependency checking
    kits = ['vtk_kit']
    cats = ['Writers']
    help = """TBD
    """

class rawVolumeRDR:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Use this module to read raw data volumes from disk.
    """

class stlRDR:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reader for simple STL triangle-based polydata format.
    """

class TIFFReader:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reads a series of TIFF files.

    Set the file pattern by making use of the file browsing dialog.  Replace
    the increasing index by a %d format specifier.  %03d can be used for
    example, in which case %d will be replaced by an integer zero padded to 3
    digits, i.e. 000, 001, 002 etc.  %d counts from the 'First slice' to the
    'Last slice'.
    """

class vtiRDR:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reader for VTK XML Image Data, the preferred format for all
    VTK-compatible image data storage.
    """

class vtkPolyDataRDR:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reader for legacy VTK polydata.
    """

class vtkStructPtsRDR:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reader for legacy VTK structured points (image) data.
    """

class vtpRDR:
    kits = ['vtk_kit']
    cats = ['Readers']
    help = """Reads VTK PolyData in the VTK XML format.

    VTP is the preferred format for DeVIDE PolyData.
    """



    
    
