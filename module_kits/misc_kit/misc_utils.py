# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import re

# map from itk type string to string
ITKTSTR_STRING = {
        'C' : 'char',
        'D' : 'double',
        'F' : 'float',
        'L' : 'long',
        'S' : 'short'
        }

# map from itk type sign to string
ITKTSGN_STRING = {
        'U' : 'unsigned',
        'S' : 'signed'
        }


def get_itk_img_type_and_dim_shortstring(itk_img):
    """Return short string representing type and dimension of itk
    image.

    This method has been put here so that it's available to non-itk
    dependent modules, such as the QuickInfo, and does not require
    any access to the ITK library itself.
    """

    # repr is e.g.:
    # <itkImagePython.itkImageSS3; proxy of <Swig Object of type 'itkImageSS3 *' at 0x6ec1570> >
    rs = repr(itk_img)
    # pick out the short code
    mo = re.search('^<itkImagePython.itkImage(.*);.*>', rs)

    if not mo:
        raise TypeError, 'This method requires an ITK image as input.'
    else:
        return mo.groups()[0]

def get_itk_img_type_and_dim(itk_img):
    """Returns itk image type as a tuple with ('type', 'dim',
    'qualifier'), e.g. ('float', '3', 'covariant vector')

    This method has been put here so that it's available to non-itk
    dependent modules, such as the QuickInfo, and does not require
    any access to the ITK library itself.
    """

    ss = get_itk_img_type_and_dim_shortstring(itk_img)
    # pull that sucker apart
    # groups:
    # 0: covariant / complex
    # 1: vector
    # 2: type shortstring
    # 3: dimensions (in case of vector, doubled up)
    mo = re.search('(C*)(V*)([^0-9]+)([0-9]+)', ss)

    c, v, tss, dim = mo.groups()
    if c and v:
        qualifier = 'covariant vector'
    elif c:
        qualifier = 'complex'
    elif v:
        qualifier = 'vector'
    else:
        qualifier = ''

    if len(tss) > 1:
        sign_string = ITKTSGN_STRING[tss[0]]
        type_string = ITKTSTR_STRING[tss[1]]
    else:
        sign_string = ''
        type_string = ITKTSTR_STRING[tss[0]]
   
    # in the case of a vector of 10-dims, does that become 1010?
    if qualifier == 'vector':
        dim_string = dim[0:len(dim) / 2]
    else:
        dim_string = dim[0]

    fss = '%s %s' % (sign_string, type_string)
    return (fss.strip(), dim_string, qualifier) 

def get_itk_img_type_and_dim_DEPRECATED(itk_img):
    """Returns itk image type as a tuple with ('type', 'dim', 'v').

    This method has been put here so that it's available to non-itk
    dependent modules, such as the QuickInfo, and does not require
    any access to the ITK library itself.
    """

    try:
        t = itk_img.this
    except AttributeError, e:
        raise TypeError, 'This method requires an ITK image as input.'
    else:
        # g will be e.g. ('float', '3') or ('unsigned_char', '2')
        # note that we use the NON-greedy version so it doesn't break
        # on vectors
        # example strings: 
        # Image.F3: _f04b4f1b_p_itk__SmartPointerTitk__ImageTfloat_3u_t_t
        # Image.VF33: _600e411b_p_itk__SmartPointerTitk__ImageTitk__VectorTfloat_3u_t_3u_t_t'
        mo = re.search('.*itk__ImageT(.*?)_([0-9]+)u*_t',
                      itk_img.this)

        if not mo:
            raise TypeError, 'This method requires an ITK Image as input.'
        else:
            g = mo.groups()
        
    # see if it's a vector
    if g[0].startswith('itk__VectorT'):
        vectorString = 'V'
        # it's a vector, so let's remove the 'itk__VectorT' bit
        g = list(g)
        g[0] = g[0][len('itk__VectorT'):]
        g = tuple(g)
        
    else:
        vectorString = ''

    # this could also be ('float', '3', 'V'), or ('unsigned_char', '2', '')
    return g + (vectorString,)

def major_axis_from_iop_cosine(iop_cosine):
    """Given an IOP direction cosine, i.e. either the row or column,
    return a tuple with two components from LRPAFH signifying the
    direction of the cosine.  For example, if the cosine is pointing from
    Left to Right (1\0\0) we return ('L', 'R').

    If the direction cosine is NOT aligned with any of the major axes,
    we return None.

    Based on a routine from dclunie's pixelmed software and info from
    http://www.itk.org/pipermail/insight-users/2003-September/004762.html
    but we've flipped some things around to make more sense.

    IOP direction cosines are always in the LPH coordinate system (patient-relative):
     * x is right to left
     * y is anterior to posterior
     * z is foot to head
    """

    obliquity_threshold = 0.8

    orientation_x = [('L', 'R'), ('R', 'L')][int(iop_cosine[0] > 0)]
    orientation_y = [('P', 'A'), ('A', 'P')][int(iop_cosine[1] > 0)]
    orientation_z = [('H', 'F'), ('F', 'H')][int(iop_cosine[2] > 0)]

    abs_x = abs(iop_cosine[0])
    abs_y = abs(iop_cosine[1])
    abs_z = abs(iop_cosine[2])

    if abs_x > obliquity_threshold and abs_x > abs_y and abs_x > abs_z:
        return orientation_x

    elif abs_y > obliquity_threshold and abs_y > abs_x and abs_y > abs_z:
        return orientation_y

    elif abs_z > obliquity_threshold and abs_z > abs_x and abs_z > abs_y:
        return orientation_z

    else:
        return None

