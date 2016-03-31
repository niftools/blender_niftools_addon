"""This script contains classes to help export nif header information."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2016, NIF File Format Library and Tools contributors.
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

user_version = {
    'OBLIVION' : 11,
    'FALLOUT_3' : 11,
    'DIVINITY_2' : 131072
}

user_version_2 = {
    'OBLIVION' : 11,
    'FALLOUT_3' : 34
}

def get_version_info(properties):

    # set user version and user version 2 for export
    b_scene = bpy.context.scene.niftools_scene

    if b_scene.user_version == 0:
        NIF_USER_VERSION = user_version.get(properties.game, 0)
    else :
        NIF_USER_VERSION = b_scene.user_version

    if b_scene.user_version_2 == 0:
        NIF_USER_VERSION_2 = user_version_2.get(properties.game, 0)
    else:
        NIF_USER_VERSION_2 = b_scene.user_version_2

    return (NIF_USER_VERSION, NIF_USER_VERSION_2)
