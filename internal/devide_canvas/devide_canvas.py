# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import vtk
from module_kits.misc_kit.mixins import SubjectMixin
from devide_canvas_object import DeVIDECanvasGlyph
import operator

import wx # we're going to use this for event handling

from module_kits.misc_kit import dprint

# think about turning this into a singleton.
class DeVIDECanvasEvent:
    def __init__(self):
        # last event information ############
        self.wx_event = None

        self.name = None

        # pos is in wx-coords, i.e. top-left is 0,0
        self.pos = (0,0)
        # last_pos and pos_delta follow same convention
        self.last_pos = (0,0)
        self.pos_delta = (0,0)

        # disp_pos is in VTK display coords: bottom-left is 0,0
        self.disp_pos = (0,0)

        self.world_pos = (0,0,0)

        # state information #################
        self.left_button = False
        self.middle_button = False
        self.right_button = False

        self.clicked_object = None

        # which cobject has the mouse
        self.picked_cobject = None
        self.picked_sub_prop = None



class DeVIDECanvas(SubjectMixin):
    """Give me a vtkRenderWindowInteractor with a Renderer, and I'll
    do the rest.  YEAH.
    """

    def __init__(self, renderwindowinteractor, renderer):

        self._rwi = renderwindowinteractor
        self._ren = renderer

        # need this to do same mouse capturing as original RWI under Win
        self._rwi_use_capture = \
                vtk.wx.wxVTKRenderWindowInteractor._useCapture

        # we can't switch on Line/Point/Polygon smoothing here,
        # because the renderwindow has already been initialised
        # we do it in main_frame.py right after we create the RWI

        # parent 2 ctor
        SubjectMixin.__init__(self)

        self._cobjects = []
        # dict for mapping from prop back to cobject
        self.prop_to_glyph = {}
        self._previousRealCoords = None
        self._potentiallyDraggedObject = None
        self._draggedObject = None

        
        self._ren.SetBackground(1.0,1.0,1.0)
        self._ren.GetActiveCamera().SetParallelProjection(1)

        # set a sensible initial zoom
        self._zoom(0.004)


        istyle = vtk.vtkInteractorStyleUser()
        #istyle = vtk.vtkInteractorStyleImage()
        self._rwi.SetInteractorStyle(istyle)

        self._rwi.Bind(wx.EVT_RIGHT_DOWN, self._handler_rd)
        self._rwi.Bind(wx.EVT_RIGHT_UP, self._handler_ru)
        self._rwi.Bind(wx.EVT_LEFT_DOWN, self._handler_ld)
        self._rwi.Bind(wx.EVT_LEFT_UP, self._handler_lu)
        self._rwi.Bind(wx.EVT_MIDDLE_DOWN, self._handler_md)
        self._rwi.Bind(wx.EVT_MIDDLE_UP, self._handler_mu)
        self._rwi.Bind(wx.EVT_MOUSEWHEEL, self._handler_wheel)
        self._rwi.Bind(wx.EVT_MOTION, self._handler_motion)

        self._rwi.Bind(wx.EVT_LEFT_DCLICK, self._handler_ldc)

        #self._rwi.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        #self._rwi.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)

        # If we use EVT_KEY_DOWN instead of EVT_CHAR, capital versions
        # of all characters are always returned.  EVT_CHAR also performs
        # other necessary keyboard-dependent translations.
        # * we unbind the char handler added by the wxRWI (else alt-w
        # for example gets interpreted as w for wireframe e.g.)
        self._rwi.Unbind(wx.EVT_CHAR)
        self._rwi.Bind(wx.EVT_CHAR, self._handler_char)
        #self._rwi.Bind(wx.EVT_KEY_UP, self.OnKeyUp)



        self._observer_ids = []

        self.event = DeVIDECanvasEvent()
        

        # do initial drawing here.

    def close(self):
        # first remove all objects
        # (we could do this more quickly, but we're opting for neatly)
        for i in range(len(self._cobjects)-1,-1,-1):
            cobj = self._cobjects[i]
            self.remove_object(cobj)

        for i in self._observer_ids:
            self._rwi.RemoveObserver(i)

        del self._rwi
        del self._ren

    # nuke this function, replace with display_to_world.
    # events are in display, everything else in world.
    # go back to graph_editor
    def eventToRealCoords_DEPRECATED(self, ex, ey):
        """Convert window event coordinates to canvas relative coordinates.
        """

        
        # get canvas parameters
        vsx, vsy = self.GetViewStart()
        dx, dy = self.GetScrollPixelsPerUnit()

        # calculate REAL coords
        rx = ex + vsx * dx
        ry = ey + vsy * dy

        return (rx, ry)

    def display_to_world(self, dpt):
        """Takes 3-D display point as input, returns 3-D world point.
        """

        # make sure we have 3 elements 
        if len(dpt) < 3:
            dpt = tuple(dpt) + (0.0,)
        elif len(dpt) > 3:
            dpt = tuple(dpt[0:3])

        self._ren.SetDisplayPoint(dpt)
        self._ren.DisplayToWorld()
        return self._ren.GetWorldPoint()[0:3]

    def world_to_display(self, wpt):
        """Takes 3-D world point as input, returns 3-D display point.
        """
        self._ren.SetWorldPoint(tuple(wpt) + (0.0,)) # this takes 4-vec
        self._ren.WorldToDisplay()
        return self._ren.GetDisplayPoint()

    def flip_y(self, y):
        return self._rwi.GetSize()[1] - y - 1

    def wx_to_world(self, wx_x, wx_y):
        disp_x = wx_x
        disp_y = self.flip_y(wx_y)
        world_depth = 0.0
        disp_z = self.world_to_display((0.0,0.0, world_depth))[2]

        wex, wey, wez = self.display_to_world((disp_x,disp_y,disp_z))

        return (wex, wey, wez)

    def _helper_handler_capture_release(self, button):
        """Helper method to be called directly after preamble
        helper in button up handlers in order to release mouse.  
        
        @param button Text description of which button was pressed,
        e.g. 'left' 
        
        """

        # if the same button is released that captured the mouse,
        # and we have the mouse, release it.  (we need to get rid
        # of this as soon as possible; if we don't and one of the
        # event handlers raises an exception, mouse is never
        # released.)
        if self._rwi_use_capture and self._rwi._own_mouse and \
                button==self._rwi._mouse_capture_button:
            self._rwi.ReleaseMouse()
            self._rwi._own_mouse = False

    def _helper_handler_capture(self, button):
        """Helper method to be called at end after button down
        helpers.

        @param button Text description of button that was pressed,
        e.g. 'left'.

        """
        # save the button and capture mouse until the button is
        # released we only capture the mouse if it hasn't already
        # been captured
        if self._rwi_use_capture and not self._rwi._own_mouse:
            self._rwi._own_mouse = True
            self._rwi._mouse_capture_button = button
            self._rwi.CaptureMouse()



    def _helper_handler_preamble(self, e, focus=True):
        e.Skip(False) 
        # Skip(False) won't search for other event
        # handlers
        self.event.wx_event = e
        if focus:
            # we need to take focus... else some other subwindow keeps it
            # once we've been there to select a module for example
            self._rwi.SetFocus()

    def _helper_glyph_button_down(self, event_name):
        ex, ey = self.event.disp_pos 
        ret = self._pick_glyph(ex,ey)
        if ret:
            pc, psp = ret
            self.event.clicked_object = pc
            self.event.name = event_name
            pc.notify(event_name)
        else:
            self.event.clicked_object = None

            # we only give the canvas the event if the glyph didn't
            # take it
            self.event.name = event_name
            self.notify(event_name)
            
    def _helper_glyph_button_up(self, event_name):
        ex, ey = self.event.disp_pos
        ret = self._pick_glyph(ex,ey)
        if ret:
            pc, psp = ret
            self.event.name = event_name
            pc.notify(event_name)
        else:
            self.event.name = event_name
            self.notify(event_name)

        # button goes up, object is not clicked anymore
        self.event.clicked_object = None

    def _handler_char(self, e):
        # we're disabling all VTK.  if we don't, the standard
        # VTK keys such as 'r' (reset), '3' (stereo) and especially
        # 'f' (fly to) can screw up things quite badly.
       
        # if ctrl, shift or alt is involved, we should pass it on to
        # wx (could be menu keys for example).
        # if not, we just eat up the event.
        if e.ControlDown() or e.ShiftDown() or e.AltDown():
            e.Skip()


    def _handler_ld(self, e):
        self._helper_handler_preamble(e)
        
        #ctrl, shift = event.ControlDown(), event.ShiftDown()
        #self._Iren.SetEventInformationFlipY(event.GetX(), event.GetY(),
        #                                    ctrl, shift, chr(0), 0, None)

        self.event.left_button = True
        self._helper_glyph_button_down('left_button_down')
        self._helper_handler_capture('l')

    def _handler_lu(self, e):
        dprint("_handler_lu::")
        self._helper_handler_preamble(e, focus=False)
        self._helper_handler_capture_release('l')
        self.event.left_button = False
        self._helper_glyph_button_up('left_button_up')

    def _handler_ldc(self, e):
        self._helper_handler_preamble(e)
        self._helper_glyph_button_down('left_button_dclick')

    def _handler_md(self, e):
        self._helper_handler_preamble(e)
        self.event.middle_button = True
        self._helper_glyph_button_down('middle_button_down')

    def _handler_mu(self, e):
        self._helper_handler_preamble(e, focus=False)
        self.event.middle_button = False
        self._helper_glyph_button_up('middle_button_up')

    def _handler_rd(self, e):
        self._helper_handler_preamble(e)
        if e.Dragging():
            return
        self.event.right_button = True
        self._helper_glyph_button_down('right_button_down')


    def _handler_ru(self, e):
        self._helper_handler_preamble(e, focus=False)
        if e.Dragging():
            return
        self.event.right_button = False
        self._helper_glyph_button_up('right_button_up')

    def _pick_glyph(self, ex, ey):
        """Give current VTK display position.
        """
        p = vtk.vtkPicker()
        p.SetTolerance(0.00001) # this is perhaps still too large

       
        for i in self._cobjects:
            if isinstance(i, DeVIDECanvasGlyph):
                for prop in i.props:
                    p.AddPickList(prop)

        p.PickFromListOn()

        ret = p.Pick((ex, ey, 0), self._ren)
        
        if ret:
            #pc = p.GetProp3Ds()
            #pc.InitTraversal()
            #prop = pc.GetNextItemAsObject()
            prop = p.GetAssembly() # for now we only want this.
            try:
                picked_cobject = self.prop_to_glyph[prop]
            except KeyError:
                dprint("_pick_glyph:: couldn't find prop in p2g dict")
                return None
            else:
                # need to find out WHICH sub-actor was picked.
                if p.GetPath().GetNumberOfItems() == 2:
                    sub_prop = \
                        p.GetPath().GetItemAsObject(1).GetViewProp()

                else:
                    sub_prop = None

                # our assembly is one level deep, so 1 is the one we
                # want (actor at leaf node)

                return (picked_cobject, sub_prop)

        return None

    def _zoom(self, amount):
        cam = self._ren.GetActiveCamera()
        if cam.GetParallelProjection():
            cam.SetParallelScale(cam.GetParallelScale() / amount)
        else:
            self._ren.GetActiveCamera().Dolly(amount)
            self._ren.ResetCameraClippingRange()
            self._ren.UpdateLightsGeometryToFollowCamera()

        self.redraw()

    def _handler_wheel(self, event):
        # wheel forward = zoom in
        # wheel backward = zoom out
        factor = [-2.0, 2.0][event.GetWheelRotation() > 0.0] 
        self._zoom(1.1 ** factor)
        #event.GetWheelDelta()


    def get_top_left_world(self):
        """Return top-left of canvas (0,0 in wx) in world coords.

        In world coordinates, top_y > bottom_y.
        """

        return self.wx_to_world(0,0)

    def get_bottom_right_world(self):
        """Return bottom-right of canvas (sizex, sizey in wx) in world
        coords.

        In world coordinates, bottom_y < top_y.
        """

        x,y = self._rwi.GetSize()
        return self.wx_to_world(x-1, y-1)

    def get_wh_world(self):
        """Return width and height of visible canvas in world
        coordinates.
        """

        tl = self.get_top_left_world()
        br = self.get_bottom_right_world()

        return br[0] - tl[0], tl[1] - br[1]

    def get_motion_vector_world(self, world_depth):
        """Calculate motion vector in world space represented by last
        mouse delta.
        """
        c = self._ren.GetActiveCamera()
       
        display_depth = self.world_to_display((0.0,0.0, world_depth))[2]

        new_pick_pt = self.display_to_world(self.event.disp_pos +
                (display_depth,))

        fy = self.flip_y(self.event.last_pos[1])
        old_pick_pt = self.display_to_world((self.event.last_pos[0], fy,
                display_depth))

        # old_pick_pt - new_pick_pt (reverse of camera!)
        motion_vector = map(operator.sub, new_pick_pt,
                old_pick_pt)

        return motion_vector


    def _handler_motion(self, event):
        """MouseMoveEvent observer for RWI.

        o contains a binding to the RWI.
        """

        #self._helper_handler_preamble(event)
        self.event.wx_event = event

        # event position is viewport relative (i.e. in pixels,
        # top-left is 0,0)
        ex, ey = event.GetX(), event.GetY() 
       
        # we need to flip Y to get VTK display coords
        self.event.disp_pos = ex, self._rwi.GetSize()[1] - ey - 1
       
        # before setting the new pos, record the delta
        self.event.pos_delta = (ex - self.event.pos[0], 
                ey - self.event.pos[1])
        self.event.last_pos = self.event.pos
        self.event.pos = ex, ey


        wex, wey, wez = self.display_to_world(self.event.disp_pos)
        self.event.world_pos = wex, wey, wez

        # add the "real" coords to the event structure
        self.event.realX = wex 
        self.event.realY = wey
        self.event.realZ = wez 

        # dragging gets preference...
        if event.Dragging() and event.MiddleIsDown() and event.ShiftDown():
            centre = self._ren.GetCenter()
            # drag up = zoom in
            # drag down = zoom out
            dyf = - 10.0 * self.event.pos_delta[1] / centre[1]
            self._zoom(1.1 ** dyf)

        elif event.Dragging() and event.MiddleIsDown():
            # move camera, according to self.event.pos_delta
            c = self._ren.GetActiveCamera()
            cfp = list(c.GetFocalPoint())
            cp = list(c.GetPosition())
            
            focal_depth = self.world_to_display(cfp)[2]

            new_pick_pt = self.display_to_world(self.event.disp_pos +
                    (focal_depth,))

            fy = self.flip_y(self.event.last_pos[1])
            old_pick_pt = self.display_to_world((self.event.last_pos[0], fy,
                    focal_depth))

            # old_pick_pt - new_pick_pt (reverse of camera!)
            motion_vector = map(operator.sub, old_pick_pt,
                    new_pick_pt)

            new_cfp = map(operator.add, cfp, motion_vector)
            new_cp = map(operator.add, cp, motion_vector)
            
            c.SetFocalPoint(new_cfp)
            c.SetPosition(new_cp)
            self.redraw()

        else: # none of the preference events want this...
            pg_ret = self._pick_glyph(ex, self.flip_y(ey))
            if pg_ret:
                picked_cobject, self.event.picked_sub_prop = pg_ret

                if self.event.left_button and event.Dragging() and \
                        self.event.clicked_object == picked_cobject:
                    # left dragging on a glyph only works if THAT
                    # glyph was clicked (and the mouse button is still
                    # down)
                    self.event.name = 'dragging'
                    if self._draggedObject is None:
                        self._draggedObject = picked_cobject
                    # the actual event will be fired further below

                if not picked_cobject is self.event.picked_cobject:
                    self.event.picked_cobject = picked_cobject
                    self.event.name = 'enter'
                    picked_cobject.notify('enter')


                else:
                    self.event.name = 'motion'
                    picked_cobject.notify('motion')


            else:
                # nothing under the mouse...
                if self.event.picked_cobject:
                    self.event.name = 'exit'
                    self.event.picked_cobject.notify('exit')
                    self.event.picked_cobject = None

            if event.Dragging() and self._draggedObject:
                # so we are Dragging() and there is a draggedObject...
                # whether draggedObject was set above, or in a
                # previous call of this event handler, we have to keep
                # on firing these drag events until draggedObject is
                # canceled.
                self.event.name = 'dragging'
                self._draggedObject.notify('dragging')

            if event.Dragging and not self._draggedObject:
                # user is dragging on canvas (no draggedObject!)
                self.event.name = 'dragging'
                self.notify(self.event.name)

        
        if not event.Dragging():
            # when user stops dragging the mouse, lose the object
            if not self._draggedObject is None:
                dprint("_handler_motion:: dragging -> off")
                self._draggedObject.draggedPort = None
                self._draggedObject = None


    def add_object(self, cobj):
        if cobj and cobj not in self._cobjects:
            cobj.canvas = self
            self._cobjects.append(cobj)
            for prop in cobj.props:
                self._ren.AddViewProp(prop)
                # we only add prop to cobject if it's a glyph
                if isinstance(cobj, DeVIDECanvasGlyph):
                    self.prop_to_glyph[prop] = cobj

            cobj.__hasMouse = False

    def redraw(self):
        """Redraw the whole scene.
        """

        self._rwi.Render()

    def update_all_geometry(self):
        """Update all geometry.

        This is useful if many of the objects states have been changed
        (e.g. new connections) and the connection visual states have
        to be updated.
        """

        for o in self._cobjects:
            o.update_geometry()

    def update_picked_cobject_at_drop(self, ex, ey):
        """Method to be used in the GraphEditor DropTarget
        (geCanvasDropTarget) to make sure that the correct glyph is
        selected.  
        
        Problem is that the application gets blocked during
        wxDropSource.DoDragDrop(), so that if the user drags things
        from for example the DICOMBrowser to a DICOMReader on the
        canvas, the canvas doesn't know that the DICOMReader has been
        picked.

        If this method is called at drop time, all is well.
        """

        pg_ret = self._pick_glyph(ex, self.flip_y(ey))
        if pg_ret:
            self.event.picked_cobject, self.event.picked_sub_prop = pg_ret

    def remove_object(self, cobj):
        if cobj and cobj in self._cobjects:
            for prop in cobj.props:
                self._ren.RemoveViewProp(prop)
            
                # it's only in here if it's a glyph
                if isinstance(cobj, DeVIDECanvasGlyph):
                    del self.prop_to_glyph[prop]

            cobj.canvas = None
            if self._draggedObject == cobj:
                self._draggedObject = None
            del self._cobjects[self._cobjects.index(cobj)]


    def reset_view(self):
        """Make sure that all actors (glyphs, connections, etc.) are
        visible.
        """
        self._ren.ResetCamera()
        self.redraw()

    def getDraggedObject(self):
        return self._draggedObject

    def getObjectsOfClass(self, classt):
        return [i for i in self._cobjects if isinstance(i, classt)]

    def getObjectWithMouse(self):
        """Return object currently containing mouse, None if no object has
        the mouse.
        """

        for cobject in self._cobjects:
            if cobject.__hasMouse:
                return cobject

        return None

    def drag_object(self, cobj, delta):
        """Move object with delta in world space.
        """

        cpos = cobj.get_position() # this gives us 2D in world space
        npos = (cpos[0] + delta[0], cpos[1] + delta[1])
        cobj.set_position(npos)
        cobj.update_geometry()

    def pan_canvas_world(self, delta_x, delta_y):
        c = self._ren.GetActiveCamera()

        cfp = list(c.GetFocalPoint())
        cfp[0] += delta_x
        cfp[1] += delta_y
        c.SetFocalPoint(cfp)

        cp = list(c.GetPosition())
        cp[0] += delta_x
        cp[1] += delta_y
        c.SetPosition(cp)

        self.redraw()



