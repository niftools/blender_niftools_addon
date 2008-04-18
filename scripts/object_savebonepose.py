#!BPY
"""
Name: 'Save Bone Pose'
Blender: 245
Group: 'Object'
Tooltip: 'Save pose of selected bones to a text buffer'
"""

# -------------------------------------------------------------------------- 
# Save Bone Pose 1.0 by Amorilia 
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

def main(arg):
    # get selected bones
    obs = [ob for ob in Blender.Object.GetSelected() if ob.type == 'Armature']
    if obs:
        boneitems = [(bonename, bone)
                     for (bonename, bone) in obs[0].getPose().bones.items()
                     if bone.sel]
    else:
        boneitems = []

    # exit if no bones selected
    if not boneitems:
        print("no bones selected in pose mode")
        Blender.Draw.PupMenu('ERROR%t|no bones selected in pose mode')
        return

    # ask for weights to delete
    PREF_BUFFER = Blender.Draw.Create("BonePose")

    pup_block = [\
    ('Text Buffer', PREF_BUFFER, 0, 20, 'The text buffer where to store the bone poses.'),\
    ]

    if not Blender.Draw.PupBlock('Save Bone Pose', pup_block):
        return
    
    # saves editmode state and exit editmode if it is enabled
    # (cannot make changes mesh data in editmode)
    is_editmode = Window.EditMode()
    Window.EditMode(0)    
    Window.WaitCursor(1)
    t = sys.time()
    
    # run script

    # open/clear text buffer
    try:
        posetxt = Blender.Text.Get(PREF_BUFFER.val)
    except NameError:
        posetxt = Blender.Text.New(PREF_BUFFER.val)
    posetxt.clear()
    for bonename, bone in boneitems:
        print("saving pose of bone %s to %s" % (bonename, PREF_BUFFER.val))
        matrix = bone.quat.toMatrix()
        matrix.resize4x4()
        matrix[3][0] = bone.loc[0]
        matrix[3][1] = bone.loc[1]
        matrix[3][2] = bone.loc[2]
        matrixtxt = ''
        for row in matrix:
            matrixtxt = '%s;%s,%s,%s,%s' % (matrixtxt,
                                            row[0], row[1], row[2], row[3])
        # matrixtxt[1:] discards the first semi-colon
        posetxt.write("%s/%s\n" % (bonename, matrixtxt[1:]))

    # report finish and timing
    print 'Save bone pose finished in %.2f seconds' % (sys.time()-t)
    Window.WaitCursor(0)
    if is_editmode:
        Window.EditMode(1)
    
if __name__ == '__main__':
    main(__script__['arg'])
