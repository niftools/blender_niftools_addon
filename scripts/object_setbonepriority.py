#!BPY
"""
Name: 'Set Bone Priority'
Blender: 245
Group: 'Object'
Tooltip: 'Set priority of selected bones'
"""

# -------------------------------------------------------------------------- 
# Set Bone Priority 1.0 by Amorilia 
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
    PREF_PRIORITY = Blender.Draw.Create(30)

    pup_block = [\
    ('Priority', PREF_PRIORITY, 0, 200, 'Bone priority.'),\
    ]

    if not Blender.Draw.PupBlock('Set Bone Priority', pup_block):
        return
    
    # saves editmode state and exit editmode if it is enabled
    # (cannot make changes mesh data in editmode)
    is_editmode = Window.EditMode()
    Window.EditMode(0)    
    Window.WaitCursor(1)
    t = sys.time()
    
    # run script
    for bonename, bone in boneitems:
        # get priorty null constraint
        print("setting bone priority on %s" % bonename)
        priorityconstr = None
        for constr in bone.constraints:
            if constr.type == Blender.Constraints.Type.NULL \
               and constr.name[:9] == "priority:":
                priorityconstr = constr
                break
        if not priorityconstr:
            priorityconstr = bone.constraints.append(
                Blender.Constraints.Type.NULL)
        priorityconstr.name = "priority:%i" % PREF_PRIORITY.val

    print 'Set bone priority finished in %.2f seconds' % (sys.time()-t)
    Window.WaitCursor(0)
    if is_editmode: Window.EditMode(1)
    
if __name__ == '__main__':
    main(__script__['arg'])
