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

from io_scene_niftools.file_io.kf import KFFile
from io_scene_niftools.modules.nif_export import armature
from io_scene_niftools.modules.nif_import.animation.transform import TransformAnimation
from io_scene_niftools.nif_common import NifCommon
from io_scene_niftools.utils import math
from io_scene_niftools.utils.singleton import NifOp
from io_scene_niftools.utils.logging import NifLog, NifError


class KfaImport(NifCommon):

    def __init__(self, operator, context):
        NifCommon.__init__(self, operator, context)

        # Helper systems
        self.transform_anim = TransformAnimation()

    def execute(self):
        """Main import function."""

        try:
            dirname = os.path.dirname(NifOp.props.filepath)
            kfa_files = [os.path.join(dirname, file.name) for file in NifOp.props.files if file.name.lower().endswith(".kfa")]
            # if an armature is present, prepare the bones for all actions
            b_armature = math.get_armature()
            if b_armature:
                # the axes used for bone correction depend on the armature in our scene
                math.set_bone_orientation(b_armature.data.niftools.axis_forward, b_armature.data.niftools.axis_up)
                # get nif space bind pose of armature here for all anims
                self.transform_anim.get_bind_data(b_armature)
            for kfa_file in kfa_files:
                kfadata = KFFile.load_kf(kfa_file)

                self.apply_scale(kfadata, NifOp.props.scale_correction)

                # calculate and set frames per second
                self.transform_anim.set_frames_per_second(kfadata.roots)
                # verify if NiNodes are present
                if len(kfadata.roots)>0 :
                    kfa_root=kfadata.roots[0]
                    # no usage identified for others NiNode, so taking care only of the first one 
                    self.transform_anim.import_kfa_root(kfa_root, b_armature)

        except NifError:
            return {'CANCELLED'}

        NifLog.info("Finished successfully")
        return {'FINISHED'}
