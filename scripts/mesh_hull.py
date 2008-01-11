#!BPY
"""
Name: 'Hull'
Blender: 244
Group: 'Mesh'
Submenu: 'Box' box
Submenu: 'Sphere' sphere
Submenu: 'Convex' convex
Tooltip: 'Hull Selected Objects'
"""

#Submenu: 'Cylinder' cylinder

# -------------------------------------------------------------------------- 
# Hull 1.1 by Amorilia 
# -------------------------------------------------------------------------- 
# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2007-2008, NIF File Format Library and Tools
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the NIF File Format Library and Tools project may not be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENCE BLOCK *****
# -------------------------------------------------------------------------- 

import Blender
from Blender import Window, sys

from PyFFI.Utils import QuickHull

def hull_box(ob, me, selected_only):
    """Hull mesh in a box."""

    # find box hull
    # todo: improve algorithm
    minx = min(v.co[0] for v in me.verts if v.sel or not selected_only)
    miny = min(v.co[1] for v in me.verts if v.sel or not selected_only)
    minz = min(v.co[2] for v in me.verts if v.sel or not selected_only)
    maxx = max(v.co[0] for v in me.verts if v.sel or not selected_only)
    maxy = max(v.co[1] for v in me.verts if v.sel or not selected_only)
    maxz = max(v.co[2] for v in me.verts if v.sel or not selected_only)

    # create box
    box = Blender.Mesh.New('box')
    for x in [minx, maxx]:
        for y in [miny, maxy]:
            for z in [minz, maxz]:
                box.verts.extend(x,y,z)
    box.faces.extend(
        [[0,1,3,2],[6,7,5,4],[0,2,6,4],[3,1,5,7],[4,5,1,0],[7,6,2,3]])

    # link box to scene and set transform
    scn = Blender.Scene.GetCurrent()
    boxob = scn.objects.new(box, 'box')
    boxob.setMatrix(ob.getMatrix('worldspace'))

    # set bounds type
    boxob.setDrawType(Blender.Object.DrawTypes['BOUNDBOX'])
    boxob.rbShapeBoundType = Blender.Object.RBShapes['BOX']

def hull_sphere(ob, me, selected_only):
    """Hull mesh in a sphere."""

    # find square box hull
    minx = min(v.co[0] for v in me.verts if v.sel or not selected_only)
    miny = min(v.co[1] for v in me.verts if v.sel or not selected_only)
    minz = min(v.co[2] for v in me.verts if v.sel or not selected_only)
    maxx = max(v.co[0] for v in me.verts if v.sel or not selected_only)
    maxy = max(v.co[1] for v in me.verts if v.sel or not selected_only)
    maxz = max(v.co[2] for v in me.verts if v.sel or not selected_only)

    cx = (minx+maxx)*0.5
    cy = (miny+maxy)*0.5
    cz = (minz+maxz)*0.5

    lx = maxx-minx
    ly = maxy-miny
    lz = maxz-minz

    l = max([lx,ly,lz])*0.5

    minx = cx-l
    miny = cy-l
    minz = cz-l
    maxx = cx+l
    maxy = cy+l
    maxz = cz+l

    # create sphere
    box = Blender.Mesh.New('sphere')
    for x in [minx, maxx]:
        for y in [miny, maxy]:
            for z in [minz, maxz]:
                box.verts.extend(x,y,z)
    box.faces.extend(
        [[0,1,3,2],[6,7,5,4],[0,2,6,4],[3,1,5,7],[4,5,1,0],[7,6,2,3]])

    # link box to scene and set transform
    scn = Blender.Scene.GetCurrent()
    boxob = scn.objects.new(box, 'sphere')
    boxob.setMatrix(ob.getMatrix('worldspace'))

    # set bounds type
    boxob.setDrawType(Blender.Object.DrawTypes['BOUNDBOX'])
    boxob.rbShapeBoundType = Blender.Object.RBShapes['SPHERE']

def hull_convex(ob, me, selected_only, precision = 0.1):
    """Hull mesh in a convex shape."""

    # find convex hull
    vertices, triangles = QuickHull.qhull3d([ tuple(v.co)
                                              for v in me.verts
                                              if v.sel or not selected_only ],
                                            precision = precision)

    # create convex mesh
    box = Blender.Mesh.New('convexpoly')
    for vert in vertices:
        box.verts.extend(*vert)
    for triangle in triangles:
        box.faces.extend(triangle)

    # link mesh to scene and set transform
    scn = Blender.Scene.GetCurrent()
    boxob = scn.objects.new(box, 'convexpoly')
    boxob.setMatrix(ob.getMatrix('worldspace'))

    # set bounds type
    boxob.drawType = Blender.Object.DrawTypes['BOUNDBOX']
    boxob.rbShapeBoundType = 5 # convex hull shape not in blender Python API; Blender.Object.RBShapes['CONVEXHULL']?
    boxob.drawMode = Blender.Object.DrawModes['WIRE']

def main(arg):
    # get selected meshes
    obs = [ob for ob in Blender.Object.GetSelected() if ob.type == 'Mesh']
    
    # saves editmode state and exit editmode if it is enabled
    # (cannot make changes mesh data in editmode)
    is_editmode = Window.EditMode()
    Window.EditMode(0)    
    Window.WaitCursor(1)
    t = sys.time()
    
    # run script
    num_affected = 0
    for ob in obs:
        me = ob.getData(mesh=1) # get Mesh, not NMesh
        # are any vertices selected?
        selected_only = is_editmode and (1 in ( vert.sel for vert in me.verts ))
        # create mesh by requested type
        if arg == 'box': hull_box(ob, me, selected_only)
        elif arg == 'sphere': hull_sphere(ob, me, selected_only)
        elif arg == 'convex':
            PREF_PRECISION = Blender.Draw.Create(0.1)
            pup_block = [
                ('Precision', PREF_PRECISION, 0.001, 2.0, 'Maximum distance by which a vertex may fall outside the hull: larger values yield simpler hulls at the expense of missing more vertices.') ]
            if not Blender.Draw.PupBlock('Convex Hull', pup_block):
                return
            hull_convex(ob, me, selected_only, precision = PREF_PRECISION.val)

    print 'Hull finished in %.2f seconds' % (sys.time()-t)
    Window.WaitCursor(0)
    if is_editmode: Window.EditMode(1)
    
if __name__ == '__main__':
    main(__script__['arg'])
