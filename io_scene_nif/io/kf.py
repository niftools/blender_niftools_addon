"""This module is used to for KeyFrame file operations"""

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


from pyffi.formats.nif import NifFormat
from io_scene_nif.utils.util_logging import NifLog
from io_scene_nif.utils.util_math import NifError


class KFFile:
    """Class to load and save a NifFile"""

    @staticmethod
    def load_kf(file_path):
        """Loads a Kf file from the given path"""
        NifLog.info("Loading {0}".format(file_path))

        kf_file = NifFormat.Data()

        # open keyframe file for binary reading
        with open(file_path, "rb") as kf_stream:
            # check if nif file is valid
            kf_file.inspect_version_only(kf_stream)
            if kf_file.version >= 0:
                # it is valid, so read the file
                NifLog.info("KF file version: {0}".format(kf_file.version, "x"))
                NifLog.info("Reading keyframe file")
                kf_file.read(kf_stream)
            elif kf_file.version == -1:
                raise NifError("Unsupported KF version.")
            else:
                raise NifError("Not a KF file.")

        return kf_file
