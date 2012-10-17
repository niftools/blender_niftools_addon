Setting Up the Build Environment
================================

.. warning::

    The following instructions are currently a work in progress.

Create a Workspace
------------------

First, create a directory to be used as your coding directory.

* ``C:\Users\<username>\workspace`` (Vista/Win 7),
* ``C:\Documents and Settings\<username>\workspace`` (XP),
* ``/home/<username>/workspace`` (Linux).

Install Blender
---------------

See :ref:`user docs <user-getblender>`.

Install Python 3.2
------------------

**Windows**

#. Download `Python 3.2 <http://www.python.org/download/releases/3.2.3/>`_.

#. Pick the installer appropriate for your platform, and follow the instructions.

#. Use the default install location.

**Fedora**::

   sudo yum install python3

**Ubuntu**::

   sudo apt-get install python3-minimal

Install Git
-----------

The code is maintained with git. If you are not yet familiar with git, read `progit <http://progit.org/book/>`_.

**Windows**

We use git bash.
Download `msysgit <http://code.google.com/p/msysgit/downloads/list>`_ and follow the installer instructions.

**Fedora**::

   sudo yum install git

**Ubuntu**::

   sudo apt-get install git

Auto CLRF
`````````

* We need to ensure consistancy between end-of-file(EOF) markers.
* This avoids excess commits where the enviroment automatically adds the EOF.
* Git will think that the whole file has been edited.
* Read `EOF <http://en.wikipedia.org/wiki/Newline>`_.
* For Windows-style line endings, use::

    git config --global core.autocrlf true

  For Unix-style line endings, use::

    git config --global core.autocrlf input

  Either option ensures that all commits in the git history
  will be stored using Unix-style endings,
  and that all checkouts (i.e. actual files)
  will have consistent line endings
  according to your operating system.

Create a Github Fork
--------------------

If you intend to work on the Blender nif plugin, first, you should
clone the code on github.

#. If you do not have one yet, `create a github account
   <https://github.com/signup/free>`_.

#. Set up your `git environment
   <http://help.github.com/set-up-git-redirect>`_.

#. `Log in <https://github.com/login>`_ on github.

#. Visit the `blender nif plugin mothership repository
   <https://github.com/neomonkeus/blender_nif_plugin>`_.

#. Click **Fork** (top right corner).

Be sure to read the remaining `github help
pages <http://help.github.com/>`_, particularly the beginner's
guides.

Get the Source Code
-------------------

To get the code, run in a terminal (linux) or in git bash (windows)::

   cd ~/workspace
   git clone --recursive git@github.com:<username>/blender_nif_plugin.git
   cd blender_nif_plugin

Optional remote tracking::

   git remote add neomonkeus git://github.com/neomonkeus/blender_nif_plugin.git
   git remote add aaron git://github.com/Aaron1178/blender_nif_plugin.git
   git remote add ghost git://github.com/Ghostwalker71/blender_nif_plugin.git
   git remote add amorilia git://github.com/amorilia/blender_nif_plugin.git

Install Build Environment Batch Script
--------------------------------------

.. note::

   * The build enviroment is a tool to standardise development for all NifTools application on Windows
   * Its purpose is to initialises a command line window with temporary enviromental setting, to avoid PATH variables.
   * It reads from a .ini file where non-standard locations path can be defined.
   * For more information, read the :file:`README.rst` file provided with the repository.

**Windows**

Get the build environment batch script::

   cd workspace
   git clone git://github.com/neomonkeus/buildenv.git

Navigate to the BuildEnv directory and create a new .ini file or using msysgit::

   cd buildenv/ini
   touch blender.ini

The following is a sample .ini file::

   arch=32
   start=workspace
   python=C:\Python32
   blender=C:\Program Files\Blender Foundation\Blender

Running Create_shortcut.bat will now add shortcuts on the Desktop for each .ini file, which when run will open a buildenv command window.


Install Pip
-----------

Pip makes it easy to install various Python modules.

**Fedora**::

   sudo yum install python3-pip

**Ubuntu/Windows**

Save `distribute_setup.py <http://python-distribute.org/distribute_setup.py>`_
and `get-pip.py <https://raw.github.com/pypa/pip/master/contrib/get-pip.py>`_
in your ``workspace`` folder.

**Windows**

Use the Build environment shortcut you just created to open the command prompt::

   python distribute_setup.py
   python get-pip.py

**Ubuntu**::

   cd ~/workfolder
   sudo python3 distribute_setup.py
   sudo python3 get-pip.py

Install Sphinx and Nose
-----------------------

**Windows** run in buildenv::

   pip-3.2 install Sphinx --target="%APPDATABLENDERADDONS%\modules"
   pip-3.2 install nose --target="%APPDATABLENDERADDONS%\modules"

.. note::

   For Blender 2.62, omit the modules part of the install path::

     pip-3.2 install Sphinx --target="%APPDATABLENDERADDONS%"
     pip-3.2 install nose --target="%APPDATABLENDERADDONS%"

**Ubuntu** run in a terminal::

   sudo apt-get install python3-nose python3-sphinx


**Fedora** run in a terminal::

   sudo yum install python3-nose python3-sphinx

Install PyFFI
-------------

The blender nif plugin require pyffi. You will need to get a
version of pyffi that works with blender::

   cd workspace
   git clone --recursive git://niftools.git.sourceforge.net/gitroot/pyffi/pyffi

**Windows** run in buildenv::

   cd /pyffi
   pip-3.2 install . --target="%APPDATABLENDERADDONS%\modules"

.. note::

   For Blender 2.62, omit the modules part of the install path::

     pip-3.2 install . --target="%APPDATABLENDERADDONS%"

**Ubuntu** run in a terminal::

   cd ~/workspace/pyffi
   pip-3.2 install . --user

**Fedora** run in a terminal::

   cd ~/workspace/pyffi
   pip-python3 install . --user

Check Installation
------------------

Now, to check that everything is installed correctly, start blender, open a Python console,
and type::

   import site
   import pyffi
   import sphinx
   import nose

You should not get any import errors.

Install Eclipse
---------------

The `Eclipse <http://www.eclipse.org/>`_ IDE allows us maintain a unified workflow for general file manipulation,
repo management, python scripting, and hooks into Blender's debugging server.


#. First install the `Java Runtime Environment <http://java.com/download>`_.

* Make sure you have the right version---on 64 bit platforms, it is safest to pick right file via `manual download <http://java.com/en/download/manual.jsp>`_.

**Windows**

#. Install `Eclipse Classic <http://www.eclipse.org/downloads/>`_

#. Unzip the file under ``C:\Program Files\eclipse``.
* If you want to create a shortcut from your desktop, right-click ``C:\Program Files\eclipse\eclipse.exe``
and select **Send to > Desktop (create shortcut)**.

**Fedora**, simply run::

   sudo yum install eclipse eclipse-egit eclipse-pydev

**Ubuntu**, simply run::

   sudo apt-get install eclipse

When starting eclipse, you are asked for your workspace folder. If you followed the
instructions above and cloned the code into ``~/workspace/blender_nif_plugin``,
then the default ``/home/<username>/workspace`` will do the trick.

At the Welcome window, click **Workbench** on the top right.

You should also install a few plugins.

* `EGit <http://eclipse.org/egit/>`_
  is an Eclipse plugin to perform git actions from within Eclipse.

  1. Go to: **Help > Install New Software > Add...**

  2. Under **Work with**, select **Indigo**.

  3. A large number of plugins will be listed. Select
     **Collaboration > Eclipse EGit**

* `PyDev <http://pydev.org/>`_
  is an Eclipse plugin targeted at Python development,
  including sytax highlighting and debugging.

  1. Go to: **Help > Install New Software > Add...**

  2. Enter the project update site:
     ``http://pydev.org/updates/``

  3. Select **PyDev**.

  4. Click **Next**, and follow the instructions.

  5. Once installed, you will be asked to configure the
     Python interpreter. Select your Python 3.2 executable
     when presented with a choice
     (``C:\Python32\python.exe`` on Windows
     and ``/usr/bin/python3`` on Fedora),
     and use **Auto Config**.

  6. Finally, you may wish to configure the eclipse editor for
     UTF-8 encoding, which is the default encoding used
     for Python code. Go to
     **Window > Preferences > General > Workspace**.
     Under **Text file encoding**, choose **Other**,
     and select **UTF-8** from the list.

* Documentation is written in `reStructuredText
  <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_.
  If you want syntax highlighting for reST,
  install the `ReST Editor plugin <http://resteditor.sourceforge.net/>`_:

  1. Go to: **Help > Install New Software > Add...**

  2. Enter the project update site:
     ``http://resteditor.sourceforge.net/eclipse``

  3. Under the ReST Editor plugin tree,
     select the ReST Editor plugin,
     and unselect the Eclipse Color Theme mapper plugin.

  4. Click **Next**, and follow the instructions.

Import Projects Into Eclipse
----------------------------

1. Make sure that the plugin's source resides in the ``blender_nif_plugin``
   folder under your workspace folder.

2. Go to: **File > Import > General > Existing Projects into Workspace**.
   Select your workspace folder as root directory, and click **Finish**.

3. For each project that you manage with Git,
   right-click on its name in the Project Explorer,
   select **Team > Share Project > Git**, and click **Next**.
   Leave **Use or create repository in parent folder of project** enabled,
   and click **Finish**.

Eclipse Debugging
-----------------

The Blender nif plugin repo comes with built-in code to link Blenders internal server with Eclipse's debug server.
This allows run-time debugging; watching the script execute, variables, function call stack etc.

Setup Eclipse PyDev Debugger
````````````````````````````
Add the Pydev Debug Perspective: **Customise Perspective -> Pydev Debug**.
Start the Pydev server.

* In the blender_nif_plugin/scripts/addon/../nifdebug.py
* If Eclipse is installed in a different folder, or each time Pydev updated.
* Edit PYDEV_SOURCE_DIR

When the plugin loads it will attempt to connect the internal server to the eclipses server.

Launching Blender from PyDev
````````````````````````````

* Go to Run->External Tools->External Tools Configuration.
* Right click on Program and select New to add a new Launch configuration
* Type in Blender for Name and select the path to blender executable under Location (f.e. Blender Foundation/Blender/blender.exe)
* Set the Working Directory to Blender Foundation/Blender
* click on Apply, then Close

Test this launch configuration by click on the Run... Toolbar icon (the one with the red toolbox).
If you have done it correctly, blender should start up.

Enable the blender plug-in and try to import one of the test nifs.
If everything works, Blender's console should be visible in Pydev's console.

* The only limitation is when want to put breakpoints in python files, you need to open the version in the Blender Foundation/Blender folder.
* You only need to this once as when you run the script, eclipse will automatically open the file once it encounters the breakpoint.

.. note::

   * When editing the repo version of the file, running install.bat will overwrite the addon version. Eclipse will as you if you want to reload the file. Ensure that you are editing the right version otherwise you might accidently overwrite you work.

Eclipse: Optional Extras
------------------------
The following are optional and levels of support varies

Command Line Completion
```````````````````````
To add in command-line completion for Blender modules, use the following stub Blender plugin repo.::

   git:// clone --recursive https://github.com/neomonkeus/blender_eclipse_debug

#. Copy the following to the Blender directory::

   ./docs/python_api/
   ./docs/refresh_python_api.bat

#. Run ``docs/refresh_python_api.bat`` to generate an updated API.
#. Link the generated API to the ``blender_nif_plugin`` project:
#. **Project > Properties > Pydev - PYTHONPATH > external libraries > .../Blender/docs/python_api/pypredef/**

.. note::
   * Variable declarations must have qualified type before auto-completion kicks in.
   * (b_obj = bpy.types.object, context = bpy.context.active_object, etc.)
   * Hovering over a variable will hot-link to the generated documentation.

* Generation of the pypredef files used from command-line completion only works with certain versions of Blender.
* Even still certain modules like BGE will not get generated.
* Currently 2.59 is the latest version that generates without error, so refer to online documentation for the most up-to-date documentation.

Happy coding & debugging.
