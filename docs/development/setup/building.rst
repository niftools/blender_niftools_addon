=============================
Building Blender from Source
=============================
.. _development-setup-buildblender:

As a developer, there are a number of advantages that come from building from source.
 * Avoid having to wait for bug fixes from full releases
 * Building the latest version to test compatibility early
 * Testing new features and how we can integrate with them
 * Blender can be built as a python module, which can improve IDE integration.

The Blender code repo is also managed by git, allowing ease of integration into our workflow.
There are some additional prerequisite utilities that need to be installed first.

See - https://wiki.blender.org/wiki/Building_Blender


.. _development-setup-buildplugin:

The repo comes with scripts which will package up the addon for use

===================================
Building the Blender Niftools Addon
===================================
The Blender Niftools Addon is a python project which can be manually put into the Blender add-ons directory.
The repo provides a set of scripts which allows creating of a zip file which can be loaded into Blender Addon Manager.

.. note::
    Ensure that you have installed the prerequisite dependencies using install_deps scripts

---------
Build Zip
---------
To build the addon from a git checkout, run the following ::

    cd ./blender_niftools_addon/install
    makezip.bat

-------
Install
-------
To install the addon from a git checkout, run the following ::

    cd ./blender_niftools_addon/install
    install.bat

or from a terminal (Linux | Ubuntu)::

    cd ./blender_niftools_addon/install
    sh ./install.sh
