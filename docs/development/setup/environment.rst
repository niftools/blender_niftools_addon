================================
Setting Up the Build Environment
================================

.. _development-design-setup-environment:

.. warning::

    The following instructions are currently a work in progress.

------------------
Create a Workspace
------------------

First, create a directory to be used as your coding directory.

 * ``C:\Users\<username>\workspace`` (Vista/Win 7).
 * ``C:\Documents and Settings\<username>\workspace`` (XP).
 * ``/home/<username>/workspace`` (Linux).


-----------
Source Code
-----------

Once you have created the directories, time to grab the source code.
See :ref:`source code <development-setup-sourcecode>` to setup source control and download the code repositories.
You will also need to download buildenv, it used to manage dependencies, needs to be updated for nix platforms.

------------------
Install Python 3.7
------------------

**Windows**

#. Download `Python 3 <http://www.python.org/download/releases/>`_.
#. Pick the installer appropriate for your platform, and follow the instructions.
#. Use the default install location. (recommended)

**Fedora**::

    sudo yum install python3

**Ubuntu**::

    sudo apt-get install python3-minimal
 
This is installed by default on 14.04 or later

---------------------
Environment Variables
---------------------

**Windows**::

    set BLENDER_ADDONS_DIR=<path_to_blender_addons>
    set BLENDER_HOME=<path_to_blender_exe>

**Ubuntu**::

    set -X BLENDER_ADDONS_DIR=<path_to_blender_addons>
    BLENDER_HOME="<path_to_blender_executable>"

**Mac**::

    export BLENDER_ADDONS_DIR="/Users/<user>/Library/Application Support/Blender/2.82/scripts/addons"
    export BLENDER_HOME="/Applications/Blender.app/Contents/MacOS"

---------------
Install Blender
---------------

See :ref:`user docs <user-getblender>`.
Alternatively, you can build Blender from source :ref:`Building Blender from Source <development-setup-buildblender>`

----------------------------
Install Develop Dependencies
----------------------------

The script will install developer dependencies in the install directory.
This enables debug support, nose documentation.

**Windows** run in buildenv::

   install_deps.bat

**Unix**::
   
   install_deps.sh
   
Using software management:

**Ubuntu** run in a terminal::

    sudo apt-get install python3-nose python3-sphinx

**Fedora** run in a terminal::

    sudo yum install python3-nose python3-sphinx
   

------------------
Check Installation
------------------

To verify everything is installed correctly, start Blender, open the internal Python console,
and type::

    import sphinx
    import nose

You should not get any import errors.
