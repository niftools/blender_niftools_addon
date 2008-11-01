#!BPY
"""
Name: 'Load Bone Pose'
Blender: 245
Group: 'Object'
Tooltip: 'Load pose of bones of selected armature from a text buffer'
"""

# -------------------------------------------------------------------------- 
# Load Bone Pose 1.0 by Amorilia 
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

def bonenamematch(name1, name2):
    """Heuristic bone name matching algorithm."""
    if name1 == name2:
        return True
    if name1.startswith("Bip01 L "):
        name1 = "Bip01 " + name1[8:] + ".L"
    elif name1.startswith("Bip01 R "):
        name1 = "Bip01 " + name1[8:] + ".R"
    if name2.startswith("Bip01 L "):
        name2 = "Bip01 " + name2[8:] + ".L"
    elif name2.startswith("Bip01 R "):
        name2 = "Bip01 " + name2[8:] + ".R"
    if name1 == name2:
        return True
    return False

def main(arg):
    # get armature and its bones
    obs = [ob for ob in Blender.Object.GetSelected() if ob.type == 'Armature']
    if obs:
        boneitems = [(bonename, bone)
                     for (bonename, bone) in obs[0].getPose().bones.items()]
    else:
        boneitems = []

    # exit if no bones selected
    if not boneitems:
        print("no armature selected")
        Blender.Draw.PupMenu('ERROR%t|no armature selected')
        return

    # ask for weights to delete
    PREF_BUFFER = Blender.Draw.Create("BonePose")

    pup_block = [\
    ('Text Buffer: ', PREF_BUFFER, 0, 20, 'The text buffer to load the bone poses from.'),\
    ]

    if not Blender.Draw.PupBlock('Load Bone Pose', pup_block):
        return
    
    # saves editmode state and exit editmode if it is enabled
    # (cannot make changes mesh data in editmode)
    is_editmode = Window.EditMode()
    Window.EditMode(0)    
    Window.WaitCursor(1)
    t = sys.time()
    
    # run script

    # open text buffer
    try:
        posetxt = Blender.Text.Get(PREF_BUFFER.val)
    except NameError:
        Blender.Draw.PupMenu('ERROR%t|text buffer does not exist')
        return
    # reconstruct poses
    for matrixtxt in posetxt.asLines():
        # skip empty lines
        if not matrixtxt:
            continue
        # reconstruct matrix from text
        bonename, matrixstr = matrixtxt.split('/')
        print("loading pose of bone %s from %s"
              % (bonename, PREF_BUFFER.val))
        try:
            matrix = Blender.Mathutils.Matrix(
                *[[float(f) for f in row.split(',')]
                  for row in matrixstr.split(';')])
        except:
            Blender.Draw.PupMenu('ERROR%t|syntax error in buffer')
            return
        # save pose matrix
        for bonename2, bone in boneitems:
            if bonenamematch(bonename, bonename2):
                bone.quat = matrix.rotationPart().toQuat()
                bone.loc = matrix.translationPart()
                break
        else:
            print("WARNING: bone %s not found in armature" % bonename)
    # display the result
    obs[0].getPose().update()

    # report finish and timing
    print 'Load bone pose finished in %.2f seconds' % (sys.time()-t)
    Window.WaitCursor(0)
    if is_editmode:
        Window.EditMode(1)
    
if __name__ == '__main__':
    main(__script__['arg'])
