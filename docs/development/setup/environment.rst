Setting Up the Build Environment
================================

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
See :ref:`source code <developer-setup-sourcecode>` to setup source control and download the code repositories.
You will also need to download buildenv, it used to manage dependancies, needs to be updated for nix platforms.
 
Install Python 3.2
------------------

**Windows**

#. Download `Python 3.2 <http://www.python.org/download/releases/3.2.3/>`_.

#. Pick the installer appropriate for your platform, and follow the instructions.

#. Use the default install location. (recommended)

**Fedora**::

   sudo yum install python3

**Ubuntu**::

   sudo apt-get install python3-minimal
 

Setup BuildEnv
--------------

In the repo is a script called create_shortcut.bat.
This creates shortcuts that when generate buildenv console, hooking to their specific ini file.

The following is a sample .ini file for the Blender Nif Plug-in::

   start=workspace
   python=<Python Directory>
   blender=<Blender Directory>
   seven_zip=<7-Zip Directory>
   pydev_debug=<Eclipse Directory>\plugins\org.python.pydev_x.x.x.xxxxxxxxxxxxxxx\pysrc
   
By default running Create_shortcut.bat adds shortcuts on the Desktop for each .ini file.

Running from command-line you can decided where it will look for .ini files and where the shortcuts get created::

   create-shortcuts.bat <ini-files>
   or
   create-shortcuts.bat <ini-files> <output_location>

Example
   create-shortcuts.bat C:\Users\<username>\workspace\bin\ini C:\Users\<username>\Desktop\shortcuts
   
  
Install Pip
-----------

Pip makes it easy to install various Python modules.

**Fedora**::

   sudo yum install python3-pip

**Ubuntu/Windows**

Save `get-pip.py <https://raw.github.com/pypa/pip/master/contrib/get-pip.py>`_
in your ``workspace`` folder.

**Windows**

Use the Build environment shortcut you just created to open the command prompt::

   python get-pip.py

**Ubuntu**::

   cd ~/workfolder
   sudo python3 get-pip.py


Install Blender
---------------

See :ref:`user docs <user-getblender>`.


Alternatively you can build blender from source :ref:`Building Blender from Source <design-setup-buildblender>`

Install Sphinx and Nose
-----------------------

**Windows** run in buildenv::

   pip install Sphinx --target="%APPDATABLENDERADDONS%\modules"
   pip install nose --target="%APPDATABLENDERADDONS%\modules"

**Ubuntu** run in a terminal::

   sudo apt-get install python3-nose python3-sphinx


**Fedora** run in a terminal::

   sudo yum install python3-nose python3-sphinx
   
   cd workspace



Check Installation
------------------

To verify everything is installed correctly, start blender, open the internal Python console,
and type::

   import sphinx
   import nose

You should not get any import errors.



