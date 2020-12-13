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

import bpy

from io_scene_niftools.file_io.egm import EGMFile
from io_scene_niftools.modules.nif_import.animation.morph import MorphAnimation
from io_scene_niftools.nif_common import NifCommon
from io_scene_niftools.utils.singleton import NifOp, EGMData
from io_scene_niftools.utils.logging import NifError, NifLog


class EgmImport(NifCommon):

    def __init__(self, operator, context):
        NifCommon.__init__(self, operator, context)

        # Helper systems
        self.morph_anim = MorphAnimation()

    def execute(self):
        """Main import function."""

        try:
            egm_path = NifOp.props.filepath

            if egm_path:
                EGMData.init(EGMFile.load_egm(egm_path))
                # scale the data
                EGMData.data.apply_scale(NifOp.props.scale_correction)
                # TODO [morph][egm] if there is an egm, the assumption is that there is only one mesh in the nif
                # grab the active object
                b_obj = bpy.context.view_layer.objects.active
                if b_obj and b_obj.type == "MESH":
                    self.morph_anim.import_egm_morphs(b_obj)
        except NifError:
            return {'CANCELLED'}

        NifLog.info("Finished successfully")
        return {'FINISHED'}
