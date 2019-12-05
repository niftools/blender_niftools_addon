"""This script contains classes to help import animations."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2013, NIF File Format Library and Tools contributors.
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

from pyffi.formats.nif import NifFormat

from io_scene_nif.modules.animation.material_export import MaterialAnimation
from io_scene_nif.modules.animation.transform_export import TransformAnimation
from io_scene_nif.modules.animation.mesh_export import MeshAnimation
from io_scene_nif.modules.animation.object_export import ObjectAnimation
from io_scene_nif.modules.animation.texture_export import TextureAnimation
from io_scene_nif.modules.object.block_registry import block_store
from io_scene_nif.utility import nif_utils
from io_scene_nif.utility.util_logging import NifLog
from io_scene_nif.utility.util_global import NifOp


def set_flags_and_timing(kfc, exp_fcurves, start_frame=None, stop_frame=None):
    # fill in the non-trivial values
    kfc.flags = 8  # active
    kfc.flags |= get_flags_from_fcurves(exp_fcurves)
    kfc.frequency = 1.0
    kfc.phase = 0.0
    if not start_frame and not stop_frame:
        start_frame, stop_frame = exp_fcurves[0].range()
    # todo [anim] this is a hack, move to scene
    kfc.start_time = start_frame / Animation.fps
    kfc.stop_time = stop_frame / Animation.fps


def get_flags_from_fcurves(fcurves):
    # see if there are cyclic extrapolation modifiers on exp_fcurves
    cyclic = False
    for fcu in fcurves:
        # sometimes fcurves can include empty fcurves - see uv controller export
        if fcu:
            for mod in fcu.modifiers:
                if mod.type == "CYCLES":
                    cyclic = True
                    break
    if cyclic:
        return 0
    else:
        return 4  # 0b100


class Animation:

    # todo [anim] this is a hack, move to scene
    fps = 30

    def __init__(self, parent):
        self.nif_export = parent
        self.obj_anim = ObjectAnimation()
        self.mat_anim = MaterialAnimation()
        self.txt_anim = TextureAnimation(parent)
        self.transform = TransformAnimation(parent)
        self.mesh_anim = MeshAnimation()
        self.fps = bpy.context.scene.render.fps

    # todo [anim] currently not used, maybe reimplement this
    @staticmethod
    def get_n_interp_from_b_interp(b_ipol):
        if b_ipol == "LINEAR":
            return NifFormat.KeyType.LINEAR_KEY
        elif b_ipol == "BEZIER":
            return NifFormat.KeyType.QUADRATIC_KEY
        elif b_ipol == "CONSTANT":
            return NifFormat.KeyType.CONST_KEY

        NifLog.warn("Unsupported interpolation mode ({0}) in blend, using quadratic/bezier.".format(b_ipol))
        return NifFormat.KeyType.QUADRATIC_KEY

    def export_text_keys(self, block_parent):
        """Parse the animation groups buffer and write an extra string data block,
        and attach it to an existing block (typically, the root of the nif tree)."""
        if NifOp.props.animation == 'GEOM_NIF':
            # animation group extra data is not present in geometry only files
            return
        anim = "Anim"
        if anim not in bpy.data.texts:
            return
        anim_txt = bpy.data.texts[anim]
        NifLog.info("Exporting animation groups")
        # -> get animation groups information

        # parse the anim text descriptor

        # the format is:
        # frame/string1[/string2[.../stringN]]

        # example:
        # 001/Idle: Start/Idle: Stop/Idle2: Start/Idle2: Loop Start
        # 051/Idle2: Stop/Idle3: Start
        # 101/Idle3: Loop Start/Idle3: Stop

        slist = anim_txt.asLines()
        flist = []
        dlist = []
        for s in slist:
            # ignore empty lines
            if not s:
                continue
            # parse line
            t = s.split('/')
            if len(t) < 2:
                raise nif_utils.NifError("Syntax error in Anim buffer ('{0}')".format(s))
            f = int(t[0])
            if (f < bpy.context.scene.frame_start) or (f > bpy.context.scene.frame_end):
                NifLog.warn("Frame in animation buffer out of range ({0} not between [{1}, {2}])".format(
                    str(f), str(bpy.context.scene.frame_start), str(bpy.context.scene.frame_end)))
            d = t[1].strip()
            for i in range(2, len(t)):
                d = d + '\r\n' + t[i].strip()
            # print 'frame %d'%f + ' -> \'%s\''%d # debug
            flist.append(f)
            dlist.append(d)

        # -> now comes the real export

        # add a NiTextKeyExtraData block, and refer to this block in the
        # parent node (we choose the root block)
        n_text_extra = block_store.create_block("NiTextKeyExtraData", anim_txt)
        block_parent.add_extra_data(n_text_extra)

        # create a text key for each frame descriptor
        n_text_extra.num_text_keys = len(flist)
        n_text_extra.text_keys.update_size()
        for i, key in enumerate(n_text_extra.text_keys):
            key.time = flist[i] / self.fps
            key.value = dlist[i]

        return n_text_extra
