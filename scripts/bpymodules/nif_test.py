"""Automated tests for the blender nif scripts."""

# ***** BEGIN LICENSE BLOCK *****
# 
# BSD License
# 
# Copyright (c) 2007-2008, NIF File Format Library and Tools
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the NIF File Format Library and Tools project may not be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENCE BLOCK *****

import Blender
from nif_import import NifImport
from nif_export import NifExport
from nif_common import NifConfig

def runtest(directory, files):
    """Test the specified files.

    @param directory: Folder where the test nif files reside.

    @param files: A list of all files to test. Each entry in the list
        is a tuple containing the filename, a dictionary of config options
        that differ from their default values, and a list of names of
        objects to select before running the import. If the dictionary
        has the key EXPORT_VERSION then the selection is exported,
        otherwise a file is imported."""
    scene = Blender.Scene.GetCurrent() # current scene
    layer = 1

    for filename, filecfg, selection in files:
        # select objects
        scene.objects.selected = [
            ob for ob in scene.objects if ob.name in selection]

        # set script configuration
        config = dict(**NifConfig.DEFAULTS)
        config["VERBOSITY"] = 99
        for key, value in filecfg.items():
            config[key] = value

        # run test
        if 'EXPORT_VERSION' in filecfg:
            # export the imported files
            print("*** exporting %s ***" % filename)

            config["EXPORT_FILE"] = "%s/%s" % (directory, filename)
            NifExport(**config)

            # increment active layer for next import
            # different tests are put into different blender layers,
            # so the results can be easily visually inspected
            layer += 1
            scene.setLayers([layer])
        else:
            print("*** importing %s ***" % filename)

            config["IMPORT_FILE"] = "%s/%s" % (directory, filename)

            # import <filename>
            print "import..."
            NifImport(**config)

    # deselect everything
    scene.objects.selected = []
    # reset active layer
    scene.setLayers([1])
