Setting Up the Build Environment
================================

.. warning::

    The following instructions are work in progress.

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

Windows

Download `Python 3.2 <http://www.python.org/download/releases/3.2.2/>`_ - 32-bit. 
Pick the installer appropriate for your platform, and follow the instructions. 
Use the default install location.

Fedora::
   
   sudo yum install python3
  
Ubuntu::
   
   sudo apt-get install python3.2

Install Git
-----------

The code is maintained with git. If you are not yet familiar with git, read `progit <http://progit.org/book/>`_.

On Windows, we use git bash. 
Download `msysgit <http://code.google.com/p/msysgit/downloads/list>`_ and follow the installer instructions.

Fedora::
   
   sudo yum install git
 
Ubuntu::
   
   sudo apt-get install git

Auto CLRF
`````````

We need to ensure consistancy between end-of-file(EOF) markers. This avoid excess commits where the enviroment automatically adds the EOF.
Read `EOF <http://en.wikipedia.org/wiki/Newline>`_.
We also enable the input flag, this autochecks any external source file introduced into the repo::

   git config --global core.autocrlf true
   git config --global core.autocrlf input


Create a Github Fork
--------------------

If you intend to work on the Blender nif scripts, first, you should
clone the code on github.

1. If you do not have one yet, `create a github account
   <https://github.com/signup/free>`_.

2. Set up your `git environment
   <http://help.github.com/set-up-git-redirect>`_.

3. `Log in <https://github.com/login>`_ on github.

4. Visit the `blender nif scripts mothership repository
   <https://github.com/amorilia/blender_nif_scripts>`_.

5. Click **Fork** (top right corner).

Be sure to read the remaining `github help
pages <http://help.github.com/>`_, particularly the beginner's
guides.

Get the Source Code
-------------------

To get the code, run in a terminal (linux) or in git bash (windows)::

   cd ~
   mkdir -p workspace
   cd workspace
   git clone --recursive git@github.com:<username>/blender_nif_scripts.git
   cd blender_nif_scripts
   git remote add amorilia git://github.com/amorilia/blender_nif_scripts.git
   git remote add neomonkeus git://github.com/neomonkeus/blender_nif_scripts.git
   cd ../

The blender nif scripts require pyffi. You will need to get a
version of pyffi that works with blender::

   git clone --recursive git://niftools.git.sourceforge.net/gitroot/pyffi/pyffi

Install Build Environment Batch Script
--------------------------------------
This is only necessary on Windows.

On Windows, get the build environment batch script::

   git clone git://github.com/amorilia/buildenv

Right-click on the ``buildenv.bat`` file, and select **Send to > Desktop (create shortcut)**.

Now right-click this newly created shortcut, and change **Target** into

Vista/Win 7::
   %comspec% /k C:\Users\<username>\workspace\buildenv\buildenv.bat C:\Python32 msvc2008 64 workspace

XP::
   %comspec% /k "C:\Documents and Settings\<username>\workspace\buildenv\buildenv.bat" C:\Python32 msvc2008 64 workspace

On 32 bit systems, type ``32`` instead of ``64``.

Install Setuptools
------------------

Setuptools makes it easy to install various Python modules.

Fedora::

   sudo yum install python3-tools

Ubuntu/Windows

Save `distribute_setup.py <http://python-distribute.org/distribute_setup.py>`_ in your ``workspace`` folder.

Windows 
Use the Python build environment shortcut you just created to open the command prompt::

   python distribute_setup.py

Ubuntu::

   cd ~/workfolder
   python distribute_setup.py
   
Install Sphinx and Nose
-----------------------

Windows, run in buildenv::

   easy_install-3.2 Sphinx
   easy_install-3.2 nose

Ubuntu, run in a terminal::

   easy_install install Sphinx
   easy_install install nose
   
Fedora, run in a terminal::

   easy_install-3.2 --user Sphinx
   sudo yum install python3-nose

Install PyFFI
-------------

On Windows, run in buildenv::

   cd pyffi
   python setup.py install
  
Ubuntu, run in a terminal::
   
   cd ~/workspace/pyffi
   python3 setup.py install --user

Fedora, run in a terminal::

   cd ~/workspace/pyffi
   python3 setup.py install --user

Update Blender Python and Check Installation
--------------------------------------------

On Windows, you'll first need to copy your entire ``C:\Python32\Lib\site-packages`` folder to
``C:\Program Files\Blender Foundation\Blender\2.60\python\lib\site-packages``.
There is a script that does this for you in buildenv::

   cd blender_nif_scripts
   copy-site-packages-to-blender.bat

Now, to check that everything is installed correctly, start blender, open a Python console,
and type::

   import site
   import pyffi
   import sphinx

You should not get any import errors.

Install Eclipse
---------------

`Eclipse <http://www.eclipse.org/>`_ provides a
bloated yet convenient environment for editing the code,
repo management, 
python scripting,
and hooks into Blender's debugging console. 

Windows,
first install the `Java Runtime Environment <http://java.com/download>`_.
Make sure you have the right version---on 64 bit platforms, it is safest
to pick right file via `manual download <http://java.com/en/download/manual.jsp>`_.
Next, install `Eclipse Classic <http://www.eclipse.org/downloads/>`_ for the windows platform.
Just unzip the file, and put it somewhere convenient, such as under ``C:\eclipse``.
If you want to create a shortcut from your desktop, right-click ``C:\eclipse\eclipse.exe``
and select **Send to > Desktop (create shortcut)**.

Fedora, simply run::

   sudo yum install eclipse

Ubuntu, simply run::

   sudo apt-get install eclipse

When starting eclipse, you are asked for your workspace folder---if you followed the
instructions above and cloned the code into ``~/workspace/blender_nif_scripts``, 
then the default ``/home/<username>/workspace`` will do the trick. 
If not, pick the folder in which the ``blender_nif_scripts`` clone resides.

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

* The documentation is written in `reStructuredText
  <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_.
  If you want syntax highlighting for reST, you must
  install the `ReST Editor plugin <http://resteditor.sourceforge.net/>`_:

  1. Go to: **Help > Install New Software > Add...**

  2. Enter the project update site:
     ``http://resteditor.sourceforge.net/eclipse``

  3. Under the ReST Editor plugin tree,
     select the ReST Editor plugin,
     and unselect the Eclipse Color Theme mapper plugin.

  4. Click **Next**, and follow the instructions.

Eclipse: Optional Extras
------------------------
 
The following is a stub repo used for Blender plugin development.::

   git:// clone --recursive https://github.com/neomonkeus/blender_eclipse_debug
   
copy the following to the Blender directory::

   ./docs/python_api/
   ./docs/refresh_python_api.bat
   run.py
   pydev_debug.py

Command Line Completion
```````````````````````

Run ``docs/refresh_python_api.bat`` to generate an updated API.
Link the generated API to the ``blender_nif_scripts`` project:
**Project > Properties > Pydev - PYTHONPATH > external libraries > .../Blender/docs/python_api/pypredef/**

.. note::
   Variable declarations must have qualified type before auto-completion kicks in
   (b_obj = bpy.types.object, context = bpy.context.active_object, etc.)

.. warning::
   Auto-completion works for the majority of the API, but some bits
   are missing, eg. Blender Game Engine.

.. note::
   Hovering over a variable will hot-link to the generated documentation.

Eclipse Debugging
`````````````````
Add the Pydev Debug: Customise Perspective -> Pydev Debug. 

.. note::
   Always start the Pydev debug server first otherwise blender will crash later. 

``pydev_debug.py`` and ``run.py`` are used to hook Eclipse's Pydev Debug to Blender's debugger.

Open ``run.py`` in Blender's text editor, under the Python console section.

Replace the strings:

* python debugger location.
* file location. 

.. note::   
   If your entry file is __init__.py file, this should be renamed to your package name while you are developing. 
   The debugger script will crash due to underscores.

Run the script; blender will appear to hang, this is as the Debugger hitting the trace() call.
Switch to Eclipses, then to the Debug Perspective, hit the continue button. 

Happy coding & debugging.
