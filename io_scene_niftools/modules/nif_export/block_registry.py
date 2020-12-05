"""This module contains helper methods to block_store objects between nif and blender objects."""

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

from pyffi.formats.nif import NifFormat

import io_scene_niftools.utils.logging
from io_scene_niftools.utils import math
from io_scene_niftools.utils.consts import BIP_01, B_L_SUFFIX, BIP01_L, B_R_SUFFIX, BIP01_R, NPC_SUFFIX, B_L_POSTFIX, \
    NPC_L, B_R_POSTFIX, BRACE_L, BRACE_R, NPC_R, OPEN_BRACKET, CLOSE_BRACKET
from io_scene_niftools.utils.logging import NifLog


def replace_blender_name(name, original, replacement, open_replace, close_replace):
    name = name.replace(original, replacement)
    name = name.replace(OPEN_BRACKET, open_replace)
    return name.replace(close_replace, CLOSE_BRACKET)


class ExportBlockRegistry:

    def __init__(self):
        self._block_to_obj = {}

    @property
    def block_to_obj(self): 
        return self._block_to_obj

    @block_to_obj.setter
    def block_to_obj(self, value):
        self._block_to_obj = value

    def register_block(self, block, b_obj=None):
        """Helper function to register a newly created block in the list of
        exported blocks and to associate it with a Blender object.

        @param block: The nif block.
        @param b_obj: The Blender object.
        @return: C{block}"""
        if b_obj is None:
            NifLog.info(f"Exporting {block.__class__.__name__} block")
        else:
            NifLog.info(f"Exporting {b_obj} as {block.__class__.__name__} block")
        self._block_to_obj[block] = b_obj
        return block

    def create_block(self, block_type, b_obj=None):
        """Helper function to create a new block, register it in the list of
        exported blocks, and associate it with a Blender object.

        @param block_type: The nif block type (for instance "NiNode").
        @type block_type: C{str}
        @param b_obj: The Blender object.
        @return: The newly created block."""
        try:
            block = getattr(NifFormat, block_type)()
        except AttributeError:
            raise io_scene_niftools.utils.logging.NifError(f"'{block_type}': Unknown block type (this is probably a bug).")
        return self.register_block(block, b_obj)

    @staticmethod
    def get_bone_name_for_nif(name):
        """Convert a bone name to a name that can be used by the nif file: turns 'Bip01 xxx.R' into 'Bip01 R xxx', and similar for L.

        :param name: The bone name as in Blender.
        :type name: :class:`str`
        :return: Bone name in nif convention.
        :rtype: :class:`str`
        """
        if isinstance(name, bytes):
            name = name.decode()
        if name.startswith(BIP_01):
            if name.endswith(B_L_SUFFIX):
                name = BIP01_L + name[6:-2]
            elif name.endswith(B_R_SUFFIX):
                name = BIP01_R + name[6:-2]
        elif name.startswith(NPC_SUFFIX) and name.endswith(B_L_POSTFIX):
            name = replace_blender_name(name, NPC_SUFFIX, NPC_L, BRACE_L, B_L_POSTFIX)
        elif name.startswith(NPC_SUFFIX) and name.endswith(B_R_POSTFIX):
            name = replace_blender_name(name, NPC_SUFFIX, NPC_R, BRACE_R, B_R_POSTFIX)
        return name

    @staticmethod
    def _get_unique_name(b_name):
        """Returns an unique name for use in the NIF file, from the name of a
        Blender object.

        :param b_name: Name of object as in blender.
        :type b_name: :class:`str`

        .. todo:: Refactor and simplify this code.
        """
        unique_name = "unnamed"
        if b_name:
            unique_name = b_name
        # blender bone naming -> nif bone naming
        unique_name = block_store.get_bone_name_for_nif(unique_name)
        return unique_name

    @staticmethod
    def get_full_name(b_obj):
        """Returns the original imported name if present, or the name by which
        the object was exported already.
        """
        longname = ""
        if b_obj:
            try:
                longname = b_obj.niftools.longname
            except:
                pass
            if not longname:
                longname = block_store._get_unique_name(b_obj.name)
        return longname


block_store = ExportBlockRegistry()
