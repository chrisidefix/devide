# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import itk
import re

from module_kits.misc_kit.misc_utils import get_itk_img_type_and_dim
from module_kits.misc_kit.misc_utils import \
        get_itk_img_type_and_dim_shortstring

get_img_type_and_dim = get_itk_img_type_and_dim
get_img_type_and_dim_shortstring = \
    get_itk_img_type_and_dim_shortstring

def coordinates_to_vector_container(points, initial_distance=0):
    """Convert list of 3-D index coordinates to an ITK
    VectorContainer for use with the FastMarching filter.

    @param points: Python iterable containing 3-D index (integer)
    coordinates.
    @param initial_distance: Initial distance that will be set on
    these nodes for the fast marching.
    """

    vc = itk.VectorContainer[itk.UI,
                             itk.LevelSetNode[itk.F, 3]].New()
    # this will clear it
    vc.Initialize()

    for pt_idx, pt in enumerate(points):
        # cast each coordinate element to integer
        x,y,z = [int(e) for e in pt]

        idx = itk.Index[3]()
        idx.SetElement(0, x)
        idx.SetElement(1, y)
        idx.SetElement(2, z)

        node = itk.LevelSetNode[itk.F, 3]()
        node.SetValue(initial_distance)
        node.SetIndex(idx)

        vc.InsertElement(pt_idx, node)

    return vc
            

def setup_itk_object_progress(dvModule, obj, nameOfObject, progressText,
                              objEvals=None, module_manager=None):
    """
    @param dvModlue: instance containing binding to obj.  Usually this
    is a DeVIDE module.  If not, remember to pass module_manager
    parameter.
    @param obj: The ITK object that needs to be progress updated.
    @param module_manager: If set, will be used as binding to
    module_manager.  If set to None, dvModule._module_manager will be
    used.  This can be used in cases when obj is NOT a member of a
    DeVIDE module, iow when dvModule is not a DeVIDE module.
    """

    # objEvals is on optional TUPLE of obj attributes that will be called
    # at each progress callback and filled into progressText via the Python
    # % operator.  In other words, all string attributes in objEvals will be
    # eval'ed on the object instance and these values will be filled into
    # progressText, which has to contain the necessary number of format tokens

    # first we have to find the attribute of dvModule that binds
    # to obj.  We _don't_ want to have a binding to obj hanging around
    # in our callable, because this means that the ITK object can never
    # be destroyed.  Instead we look up the binding everytime the callable
    # is invoked by making use of getattr on the devideModule binding.

    # find attribute string of obj in dvModule
    di = dvModule.__dict__.items()
    objAttrString = None
    for key, value in di:
        if value is obj:
            objAttrString = key
            break

    if not objAttrString:
        raise Exception, 'Could not determine attribute string for ' \
              'object %s.' % (obj.__class__.__name__)

    if module_manager is None:
        mm = dvModule._module_manager
    else:
        mm = module_manager

    # sanity check objEvals
    if type(objEvals) != type(()) and objEvals != None:
        raise TypeError, 'objEvals should be a tuple or None.'

    def commandCallable():
        # setup for and get values of all requested objEvals
        values = []

        if type(objEvals) == type(()):
            for objEval in objEvals:
                values.append(
                    eval('dvModule.%s.%s' % (objAttrString, objEval)))

        values = tuple(values)

        # do the actual callback
        mm.generic_progress_callback(getattr(dvModule, objAttrString),
            nameOfObject, getattr(dvModule, objAttrString).GetProgress(),
            progressText % values)

        # get rid of all bindings
        del values

    pc = itk.PyCommand.New()
    pc.SetCommandCallable(commandCallable)
    res = obj.AddObserver(itk.ProgressEvent(), pc.GetPointer())

    # we DON'T have to store a binding to the PyCommand; during AddObserver,
    # the ITK object makes its own copy.  The ITK object will also take care
    # of destroying the observer when it (the ITK object) is destroyed
    #obj.progressPyCommand = pc

setupITKObjectProgress = setup_itk_object_progress
