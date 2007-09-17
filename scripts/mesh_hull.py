#!BPY
"""
Name: 'Hull'
Blender: 244
Group: 'Mesh'
Submenu: 'Box' box
Submenu: 'Sphere' sphere
Submenu: 'Cylinder' cylinder
Tooltip: 'Hull Selected Objects'
"""

# note: this script is not quite functional yet

# -------------------------------------------------------------------------- 
# Hull 1.0 by Amorilia 
# -------------------------------------------------------------------------- 
# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2007, NIF File Format Library and Tools
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

def hull_box(me):
    """Hull mesh in a box."""

    # find box hull
    best_face = me.faces[0]
    for f in me.faces:
        # find box along this face
        # first find face normal
        n = f.no
        #for v in me.vertices:
        #   pass 

def main():
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
        hull_box(me)

    print 'Hull finished in %.2f seconds' % (sys.time()-t)
    Window.WaitCursor(0)
    if is_editmode: Window.EditMode(1)
    
if __name__ == '__main__':
    main()
