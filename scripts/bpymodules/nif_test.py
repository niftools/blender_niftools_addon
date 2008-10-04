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

class Test:
    """A single test, describing import or export of a file."""
    def __init__(self, filename = None, config = None, selection = None):
        """Initializes a test.

        @param filename: The name of the file to test.
        @type filename: C{str}
        @param config: Configuration options that differ from their default
            values. If the dictionary has the key EXPORT_VERSION then the
            selection is exported, otherwise a file is imported.
        @type config: C{dict}
        @param selection: List of names of objects to select before running
            the test.
        @type selection: C{list} of C{str}
        """
        if filename is None:
            raise ValueError("A test must specify a filename.")
        self.filename = filename
        self.config = config if not(config is None) else {}
        self.selection = selection if not(selection is None) else []

class TestSuite:
    """A test suite class.

    @cvar FOLDER: The folder where all files for this test reside.
    @type FOLDER: C{str}
    @cvar SCRIPTS: List of L{Test} instances which describe the files which
        are imported and exported, along with options and objects to be
        selected.
    @type SCRIPTS: C{list} of L{Test}
    @ivar data: Dictionary mapping file name to L{NifExport} or L{NifImport}
        instances.
    @type data: C{dict}
    """
    FOLDER = ""
    TESTS = []
    def __init__(self):
        self.data = {}

    def run(self):
        """Test the files in L{FOLDER} specified by L{TESTS}."""
        scene = Blender.Scene.GetCurrent() # current scene
        layer = 1

        for test in self.TESTS:
            filename = test.filename

            # select objects
            scene.objects.selected = [
                ob for ob in scene.objects if ob.name in test.selection]

            # set script configuration
            config = dict(**NifConfig.DEFAULTS)
            config["VERBOSITY"] = 99
            for key, value in test.config.items():
                config[key] = value

            # run test
            if 'EXPORT_VERSION' in test.config:
                # export the imported files
                print("*** exporting %s ***" % filename)

                config["EXPORT_FILE"] = "%s/%s" % (self.FOLDER, filename)
                self.data[filename] = NifExport(**config)

                # increment active layer for next import
                # different tests are put into different blender layers,
                # so the results can be easily visually inspected
                layer += 1
                scene.setLayers([layer])
            else:
                print("*** importing %s ***" % filename)

                config["IMPORT_FILE"] = "%s/%s" % (self.FOLDER, filename)

                # import <filename>
                print "import..."
                self.data[filename] = NifImport(**config)

            # callback after every import/export
            self.test_callback(filename)

        # deselect everything
        scene.objects.selected = []
        # reset active layer
        scene.setLayers([1])

    def test_callback(self, filename):
        """Called after every import or export."""
        return

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
