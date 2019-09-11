"""This script imports Netimmerse/Gamebryo nif files to Blender."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2005-2015, NIF File Format Library and Tools contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

from io_scene_nif.nif_common import NifCommon
from io_scene_nif.io.kf import KFFile
from io_scene_nif.modules import armature
from io_scene_nif.modules.animation.animation_import import AnimationHelper
from io_scene_nif.utility.nif_global import NifOp
from io_scene_nif.utility import nif_utils
import pyffi.spells.nif.fix
from pyffi.formats.nif import NifFormat
import bpy
import os

class KfImport(NifCommon):

    def __init__(self, operator, context):
        NifCommon.__init__(self, operator)
        
        # Helper systems
        self.animationhelper = AnimationHelper(parent=self)
             
    def execute(self):
        """Main import function."""

        dirname = os.path.dirname(NifOp.props.filepath)
        kf_files = [os.path.join(dirname, file.name) for file in NifOp.props.files if file.name.lower().endswith(".kf")]
        b_armature = armature.get_armature()
        if not b_armature:
            raise nif_utils.NifError("No armature was found in scene, can not import KF animation!")
        
        #the axes used for bone correction depend on the armature in our scene
        armature.set_bone_orientation(b_armature.data.niftools.axis_forward, b_armature.data.niftools.axis_up)
        
        #get nif space bind pose of armature here for all anims
        bind_data = armature.get_bind_data(b_armature)
        for kf_file in kf_files:
            kfdata = KFFile.load_kf(kf_file)
            # use pyffi toaster to scale the tree
            toaster = pyffi.spells.nif.NifToaster()
            toaster.scale = NifOp.props.scale_correction_import
            pyffi.spells.nif.fix.SpellScale(data=kfdata, toaster=toaster).recurse()
            # calculate and set frames per second
            self.animationhelper.set_frames_per_second( kfdata.roots )
            for kf_root in kfdata.roots:
                self.animationhelper.armature_animation.import_kf_standalone( kf_root, b_armature, bind_data )
        return {'FINISHED'}