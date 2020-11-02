"""This script imports Netimmerse/Gamebryo nif files to Blender."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2019, NIF File Format Library and Tools contributors.
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

import os

import pyffi.spells.nif.fix

from io_scene_nif.file_io.kf import KFFile
from io_scene_nif.modules.nif_export import armature
from io_scene_nif.modules.nif_import.animation.transform import TransformAnimation
from io_scene_nif.nif_common import NifCommon
from io_scene_nif.utils import util_math
from io_scene_nif.utils.util_global import NifOp


class KfImport(NifCommon):

    def __init__(self, operator, context):
        NifCommon.__init__(self, operator, context)

        # Helper systems
        self.tranform_anim = TransformAnimation()

    def execute(self):
        """Main import function."""

        dirname = os.path.dirname(NifOp.props.filepath)
        kf_files = [os.path.join(dirname, file.name) for file in NifOp.props.files if file.name.lower().endswith(".kf")]
        b_armature = util_math.get_armature()
        if not b_armature:
            raise util_math.NifError("No armature was found in scene, can not import KF animation!")

        # the axes used for bone correction depend on the armature in our scene
        util_math.set_bone_orientation(b_armature.data.niftools.axis_forward, b_armature.data.niftools.axis_up)

        # get nif space bind pose of armature here for all anims
        bind_data = armature.get_bind_data(b_armature)
        for kf_file in kf_files:
            kfdata = KFFile.load_kf(kf_file)

            # use pyffi toaster to scale the tree
            toaster = pyffi.spells.nif.NifToaster()
            toaster.scale = NifOp.props.scale_correction_import
            pyffi.spells.nif.fix.SpellScale(data=kfdata, toaster=toaster).recurse()

            # calculate and set frames per second
            self.tranform_anim.set_frames_per_second(kfdata.roots)
            for kf_root in kfdata.roots:
                self.tranform_anim.import_kf_root(kf_root, b_armature, bind_data)
        return {'FINISHED'}
