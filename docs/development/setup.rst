Setting Up the Build Environment
================================

.. warning::

    The following instructions are work in progress.

Create a Workspace
------------------

First, create a directory to be used as your coding directory.
If you plan to use eclipse, use:

* ``C:\Users\<username>\workspace`` (Vista/Win 7),
* ``C:\Documents and Settings\<username>\workspace`` (XP), or
* ``/home/<username>/workspace`` (Linux).

Install Blender
---------------

See :ref:`user docs <user-getblender>`.

Install Python 3.2
------------------

On Windows,
download `Python 3.2 <http://www.python.org/download/releases/3.2.2/>`_ (pick the
installer appropriate for your platform), and
follow the instructions. Use the default install location.

On Fedora, simply run::

  sudo yum install python3

Install Git
-----------

The code is maintained with git. If you are not yet familiar with git,
read `progit <http://progit.org/book/>`_.

On Windows, we use git bash. Download
`msysgit <http://code.google.com/p/msysgit/downloads/list>`_
and follow the installer instructions.

On Fedora, simply run::

  sudo yum install git

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
  git clone git@github.com:<username>/blender_nif_scripts.git
  cd blender_nif_scripts
  git remote add amorilia git://github.com/amorilia/blender_nif_scripts.git
  git remote add neomonkeus git://github.com/neomonkeus/blender_nif_scripts.git
  cd ..

The blender nif scripts require pyffi. You will need to get a
version of pyffi that works with blender::

  git clone --recursive git://niftools.git.sourceforge.net/gitroot/pyffi/pyffi

On Windows, also get the build environment batch script::

  git clone git://github.com/amorilia/buildenv

Install Build Environment Batch Script
--------------------------------------

This is only necessary on Windows.

Right-click on the ``buildenv.bat`` file,
and select **Send to > Desktop (create shortcut)**.

Now right-click this newly created shortcut,
and change **Target** into::

  %comspec% /k C:\Users\<username>\workspace\buildenv.bat C:\Python32 msvc2008 64 workspace

on Vista/Win 7, or::

  %comspec% /k "C:\Documents and Settings\<username>\workspace\buildenv.bat" C:\Python32 msvc2008 64 workspace

on XP. On 32 bit systems, type ``32`` instead of ``64``.

Install Setuptools
------------------

Setuptools makes it easy to install various Python modules.

On Fedora, simply run::

  sudo yum install python3-tools

On Windows,
save `distribute_setup.py
<http://python-distribute.org/distribute_setup.py>`_ 
in your ``workspace`` folder,
double click on the Python build environment shortcut you just created,
and type::

  python distribute_setup.py

Install Sphinx and Nose
-----------------------

On Windows, run in buildenv::

  easy_install install Sphinx
  easy_install install nose

On Fedora, run in a terminal::

  easy_install-3.2 --user Sphinx
  sudo yum install python3-nose

Install PyFFI
-------------

On Windows, run in buildenv::

  cd pyffi
  python setup.py install

On Fedora, run in a terminal::

  cd ~/workspace/pyffi
  python3 setup.py install --user

Update Blender Python and Check Installation
--------------------------------------------

On Windows, you'll first need to
copy your entire ``C:\Python32\Lib\site-packages`` folder to
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

On Windows,
first install the `Java Runtime Environment <http://java.com/download>`_.
Make sure you have the right version---on 64 bit platforms, it is safest
to pick right file via `manual download <http://java.com/en/download/manual.jsp>`_.
Next, install `Eclipse Classic <http://www.eclipse.org/downloads/>`_ for the windows platform.
Just unzip the file, and put it somewhere convenient, such as under ``C:\eclipse``.
If you want to create a shortcut from your desktop, right-click ``C:\eclipse\eclipse.exe``
and select **Send to > Desktop (create shortcut)**.

On Fedora, simply run::

  sudo yum install eclipse-pydev eclipse-egit

When starting eclipse,
you are asked for your workspace folder---if you followed the
instructions above and cloned the code into
``~/workspace/blender_nif_scripts``, then the default
``/home/<username>/workspace`` will do the trick. If not, pick the
folder in which the ``blender_nif_scripts`` clone resides.

At the Welcome window, click **Workbench** on the top right.

You should also install a few plugins. On Fedora,
you already have EGit and PyDev if you followed
the instructions above, so you only need
to configure your PyDev Python interpreter,
and the ReST Editor plugin.

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

Eclipse: Blender Extras
-----------------------

.. todo::

   Update for actual location
   of command line completion code.

Once you have cloned this Repo to your local,
copy the following to the Blender directory::

    ./docs/python_api/
    ./docs/refresh_python_api.bat
    run.py
    pydev_debug.py

Command Line Completion
~~~~~~~~~~~~~~~~~~~~~~~

Run ``docs/refresh_python_api.bat`` to generate an updated API
and link the generated API
to the ``blender_nif_scripts`` project:
**Project > Properties > Pydev - PYTHONPATH > external libraries > .../Blender/docs/python_api/pypredef/**

.. note::

   Type declarations must be fully qualified
   (bpy.types.object, bpy.context.active_object, etc.)
   before auto-completion kicks in

.. note::

   Hovering over a variable will hot-link to the generated documentation.

.. warning::

   Auto-completion works for the majority of the API, but some bits
   are missing.

Debugging
~~~~~~~~~

``pydev_debug.py`` and ``run.py``
hook Eclipse's Pydev Debug to Blender's debugger.

Add the Pydev Debug: Customise Perspective -> Pydev Debug. 
Always start the Pydev debug server first otherwise blender will crash later.	

Open the ``test/blend/debug.blend`` file 

Open ``run.py`` in the scripting text editor.

Replace the strings:

1. python debugger location.

2. main execution file location.

Run the script; blender will appear to hang but this is as the Debugger has hit the trace() call

In Eclipse switch to debug mode and begin scripting.
