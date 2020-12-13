"""This module contains helper methods to block_store objects between nif and blender objects."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2020, NIF File Format Library and Tools contributors.
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

from io_scene_niftools.utils.logging import NifLog

from io_scene_niftools.utils.consts import BIP_01, BIP01_L, B_L_SUFFIX, BIP01_R, B_R_SUFFIX, NPC_L, NPC_R, NPC_SUFFIX, \
    BRACE_R, B_R_POSTFIX, B_L_POSTFIX, CLOSE_BRACKET, BRACE_L, OPEN_BRACKET


def get_bone_name_for_blender(name):
    """Convert a bone name to a name that can be used by Blender: turns 'Bip01 R xxx' into 'Bip01 xxx.R', and similar for L.

    :param name: The bone name as in the nif file.
    :type name: :class:`str`
    :return: Bone name in Blender convention.
    :rtype: :class:`str`
    """
    if isinstance(name, bytes):
        name = name.decode()
    if name.startswith(BIP01_L):
        name = BIP_01 + name[8:] + B_L_SUFFIX
    elif name.startswith(BIP01_R):
        name = BIP_01 + name[8:] + B_R_SUFFIX
    elif name.startswith(NPC_L) and name.endswith(CLOSE_BRACKET):
        name = replace_nif_name(name, NPC_L, NPC_SUFFIX, BRACE_L, B_L_POSTFIX)
    elif name.startswith(NPC_R) and name.endswith(CLOSE_BRACKET):
        name = replace_nif_name(name, NPC_R, NPC_SUFFIX, BRACE_R, B_R_POSTFIX)
    return name


def replace_nif_name(name, original, replacement, open_replace, close_replace):
    name = name.replace(original, replacement)
    name = name.replace(open_replace, OPEN_BRACKET)
    return name.replace(CLOSE_BRACKET, close_replace)


class BlockRegistry:

    @staticmethod
    def store_longname(b_obj, n_name):
        """Save original name as object property, for export"""
        if b_obj.name != n_name:
            b_obj.niftools.longname = n_name
            NifLog.debug(f"Stored long name for {b_obj.name}")

    @staticmethod
    def import_name(n_block):
        """Get name of n_block, ready for blender but not necessarily unique.

        :param n_block: A named nif block.
        :type n_block: :class:`~pyffi.formats.nif.NifFormat.NiObjectNET`
        """
        if n_block is None:
            return ""

        NifLog.debug(f"Importing name for {n_block.__class__.__name__} block from {n_block.name}")

        n_name = n_block.name.decode()

        # if name is empty, create something non-empty
        if not n_name:
            n_name = "noname"
        n_name = get_bone_name_for_blender(n_name)

        return n_name


block_store = BlockRegistry()
