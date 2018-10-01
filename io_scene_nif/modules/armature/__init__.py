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


def get_bone_name_for_blender(name):
    """Convert a bone name to a name that can be used by Blender: turns
    'Bip01 R xxx' into 'Bip01 xxx.R', and similar for L.

    :param name: The bone name as in the nif file.
    :type name: :class:`str`
    :return: Bone name in Blender convention.
    :rtype: :class:`str`
    """
    if isinstance(name, bytes):
        name = name.decode()
    if name.startswith("Bip01 L "):
        return "Bip01 " + name[8:] + ".L"
    elif name.startswith("Bip01 R "):
        return "Bip01 " + name[8:] + ".R"
    elif name.startswith("NPC L ") and name.endswith("]"):
        name = name.replace("NPC L", "NPC")
        name = name.replace("[L", "[")
        name = name.replace("]", "].L")
        return name
    elif name.startswith("NPC R ") and name.endswith("]"):
        name = name.replace("NPC R", "NPC")
        name = name.replace("[R", "[")
        name = name.replace("]", "].R")
        return name

    return name


def get_bone_name_for_nif(name):
    """Convert a bone name to a name that can be used by the nif file:
    turns 'Bip01 xxx.R' into 'Bip01 R xxx', and similar for L.

    :param name: The bone name as in Blender.
    :type name: :class:`str`
    :return: Bone name in nif convention.
    :rtype: :class:`str`
    """
    if isinstance(name, bytes):
        name = name.decode()
    if name.startswith("Bip01 "):
        if name.endswith(".L"):
            return "Bip01 L " + name[6:-2]
        elif name.endswith(".R"):
            return "Bip01 R " + name[6:-2]
    elif name.startswith("NPC ") and name.endswith("].L"):
        name = name.replace("NPC ", "NPC L")
        name = name.replace("[", "[L")
        name = name.replace("].L", "]")
        return name
    elif name.startswith("NPC ") and name.endswith("].R"):
        name = name.replace("NPC ", "NPC R")
        name = name.replace("[", "[R")
        name = name.replace("].R", "]")
        return name
    return name
