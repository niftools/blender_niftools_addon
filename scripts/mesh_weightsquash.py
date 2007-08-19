#!BPY
"""
Name: 'Weight Squash'
Blender: 244
Group: 'Mesh'
Tooltip: 'Squash Vertex Weights'
"""

# -------------------------------------------------------------------------- 
# Squash Weights 1.0 by Amorilia 
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

def weight_squash(me, cutoff = 0.02, nbones = 3):
    """Remove vertices from vertex group if their weight is less than cutoff.
    The affected vertices are selected in editmode for further inspection if
    required.
    
    Returns number of vertices affected."""

    num_affected = 0

    # deselect all vertices
    for v in me.verts:
        v.sel = 0

    # remove weights
    for group in me.getVertGroupNames():
        print "=== %s ==="%group
        
        vert_list = me.getVertsFromGroup(group, 1) # second argument = 1 means also return vertex weights
        remove_list = [v[0] for v in vert_list if v[1] < cutoff]
        remove_list = [i for i in remove_list if len(me.getVertexInfluences(i)) > nbones]
        me.removeVertsFromGroup(group, remove_list)
        num_affected += len(remove_list)

        # inform user
        if remove_list:
            print "removed"
            print remove_list

        # select affected vertices
        for i in remove_list:
            me.verts[i].sel = 1

    return num_affected

def main():
    # get selected meshes
    obs = [ob for ob in Blender.Object.GetSelected() if ob.type == 'Mesh']
    
    # ask for weights to delete
    PREF_CUTOFF = Blender.Draw.Create(0.02)
    PREF_NBONES = Blender.Draw.Create(3)
    
    pup_block = [\
    ('Weight Cutoff', PREF_CUTOFF, 0.001, 0.499, 'Vertices with weight less than this number will be deleted from the vertex group.'),\
    ('Min Bones', PREF_NBONES, 1, 4, 'Only delete from vertex group if number of bone influences is larger than this number.'),\
    ]
    
    if not Blender.Draw.PupBlock('Vertex Squash', pup_block):
        return
    
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
        num_affected += weight_squash(me, cutoff = PREF_CUTOFF.val, nbones = PREF_NBONES.val)

    print 'Weight Squash finished in %.2f seconds' % (sys.time()-t)
    print '%i vertices removed from groups'%num_affected
    Window.WaitCursor(0)
    if is_editmode: Window.EditMode(1)
    
if __name__ == '__main__':
    main()
