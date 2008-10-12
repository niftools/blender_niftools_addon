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

class TestSuite:
    """A test suite class.

    @ivar scene: The Blender scene for this test suite.
    @type scene: Blender.Scene.Scene
    @ivar layer: The current Blender layer in the scene.
    @type layer: C{int}
    """
    def __init__(self, name):
        """Initialize a new test suite with given name.

        @param name: The name of the test (will be used as name of the scene
            for this test).
        @type name: C{str}
        """
        self.scene = Blender.Scene.New(name) # new scene
        self.layer = 1 # current layer

        # set active scene
        self.scene.makeCurrent()
        # set active layer
        self.scene.setLayers([self.layer])

    def test(self, filename = None, config = None, selection = None):
        """Run given test, and increase layer after export.

        @param filename: The name of the file to test.
        @type filename: C{str}
        @param config: Configuration options that differ from their default
            values. If the dictionary has the key EXPORT_VERSION then the
            selection is exported, otherwise a file is imported. Optional.
        @type config: C{dict}
        @param selection: List of names of objects to select before running
            the test. Optional.
        @type selection: C{list} of C{str}
        @return: The import or export object.
        @rtype: L{NifImport} or L{NifExport}
        """

        if filename is None:
            raise ValueError("A test must specify a filename.")
        if config is None:
            config = {}
        if selection is None:
            selection = []

        # select objects
        self.scene.objects.selected = [
            ob for ob in self.scene.objects if ob.name in selection]
        print [ob for ob in self.scene.objects.selected]

        # set script configuration
        finalconfig = dict(**NifConfig.DEFAULTS)
        finalconfig["VERBOSITY"] = 99
        for key, value in config.items():
            finalconfig[key] = value

        # run test
        if 'EXPORT_VERSION' in config:
            # export the imported files
            print("*** exporting %s ***" % filename)

            finalconfig["EXPORT_FILE"] = filename
            result = NifExport(**finalconfig)

            # increment active layer for next import
            # different tests are put into different blender layers,
            # so the results can be easily visually inspected
            self.layer += 1
            self.scene.setLayers([self.layer])

            # return test result
            return result
        else:
            print("*** importing %s ***" % filename)

            # import file and return test result
            finalconfig["IMPORT_FILE"] =  filename
            return NifImport(**finalconfig)

    def run(self):
        """Run the test suite. Override."""
        raise NotImplementedError

def runtest(directory, files):
    """Test the specified files.

    @deprecated: Derive your tests from the L{TestSuite} class instead!
    @param directory: Folder where the test nif files reside.

    @param files: A list of all files to test. Each entry in the list
        is a tuple containing the filename, a dictionary of config options
        , and a list of names of
        objects to select before running the import.
    """
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
