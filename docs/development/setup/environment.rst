Setting Up the Build Environment
================================

.. _development-design-setup-environment:

.. warning::

    The following instructions are currently a work in progress.

Create a Workspace
------------------

First, create a directory to be used as your coding directory.

 * ``C:\Users\<username>\workspace`` (Vista/Win 7).
 * ``C:\Documents and Settings\<username>\workspace`` (XP).
 * ``/home/<username>/workspace`` (Linux).


Source Code
-----------

Once you have created the directories, time to grab the source code.
See :ref:`source code <development-setup-sourcecode>` to setup source control and download the code repositories.
You will also need to download buildenv, it used to manage dependencies, needs to be updated for nix platforms.
 
Install Python 3.4
------------------

**Windows**

#. Download `Python 3.4 <http://www.python.org/download/releases/3.2.3/>`_.
#. Pick the installer appropriate for your platform, and follow the instructions.
#. Use the default install location. (recommended)

**Fedora**::

   sudo yum install python3

**Ubuntu**::

   sudo apt-get install python3-minimal
 
This is installed by default on 14.04 or later

Environment Variables
--------------

**Windows**::

   set /p BLENDER_ADDONS_DIR=<path_to_blender_addons>

**Ubuntu**::

   set -X BLENDER_ADDONS_DIR=<path_to_blender_addons>

Install Blender
---------------

See :ref:`user docs <user-getblender>`.
Alternatively, you can build Blender from source :ref:`Building Blender from Source <development-setup-buildblender>`

Install Sphinx and Nose
-----------------------

Dependency scripts are available in the install directory.

**Windows** run in buildenv::

   install_deps.bat

**Unix**::
   
   install_deps.sh
   
Using software management:

**Ubuntu** run in a terminal::

   sudo apt-get install python3-nose python3-sphinx

**Fedora** run in a terminal::

   sudo yum install python3-nose python3-sphinx
   

Check Installation
------------------

To verify everything is installed correctly, start Blender, open the internal Python console,
and type::

   import sphinx
   import nose

You should not get any import errors.
