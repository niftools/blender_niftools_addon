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

Fedora
``````

For Fedora 16 and up, Blender 2.5x is available via yum::

  sudo yum install blender

For Fedora 15, first `setup a development environment
<http://fedoraproject.org/wiki/How_to_create_an_RPM_package>`_::

  sudo yum groupinstall "Development Tools" -y
  sudo yum install rpmdevtools -y
  rpmdev-setuptree

Then, clone the spec file, install the sources, install the build
dependencies, and kick off an rpm build::

  git clone git://pkgs.fedoraproject.org/blender
  cd blender
  cp * ~/rpmbuild/SOURCES/
  wget http://download.blender.org/source/blender-2.60a.tar.gz
  mv blender-2.60a.tar.gz ~/rpmbuild/SOURCES/
  cat blender.spec | grep ^BuildRequires | gawk '{ print $2 }' | xargs sudo yum install -y
  rpmbuild -ba blender.spec

Building blender takes a long time. When the build is finished,
install the rpm::

  sudo yum localinstall ~/rpmbuild/RPMS/x86_64/blender-2.60a-3.fc15.x86_64.rpm

.. warning::

   The package upgrades Blender 2.49b, so if you had it installed
   previously, it will no longer be available. Do::

     sudo yum erase blender
     sudo yum install blender

   to get your old Blender 2.49b back.

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
   <https://github.com/niftools/blender_nif_plugin>`_.

#. Click **Fork** (top right corner).

Be sure to read the remaining `github help
pages <http://help.github.com/>`_, particularly the beginner's
guides.

Setup SSH Keys
--------------

Follow the instructions at `Github's SSH Page <https://github.com/login>`_.

.. note::

   * If you run into errors while starting the ssh-agent or adding the keys to the ssh-agent try running "eval `ssh-agent -s`".

Get the Source Code
-------------------

To get the code, run in a terminal (linux) or in git bash (windows)::

   cd ~/workspace
   git clone --recursive git@github.com:<username>/blender_nif_plugin.git
   cd blender_nif_plugin

We use submodules to point to the external repository. 
This avoids having to internally store & maintain seperate code bases.

Fetching the submodules::
   
   $ git submodule update --init
   
If you get the following error::

   fatal: Needed a single revision 
   Unable to find current revision in submodule path ’pyffi’

Run::
   
   $ rm -rf pyffi   
   $ git submodule update --init

Optional remote tracking::

   git remote add neomonkeus git://github.com/neomonkeus/blender_nif_plugin.git
   git remote add aaron git://github.com/Aaron1178/blender_nif_plugin.git
   git remote add ghost git://github.com/Ghostwalker71/blender_nif_plugin.git
   git remote add amorilia git://github.com/amorilia/blender_nif_plugin.git

Install Build Environment Batch Script
--------------------------------------

.. note::

   * The build enviroment is a tool to standardise development for all NifTools application on Windows
   * Its purpose is to initialises a command line window with temporary enviromental setting, avoiding bloating PATH.
   * It will attempt to look for supported build utilities which can also be read from an .ini file 
   * For more information, read the :file:`README.rst` file provided with the repository.

**Windows**

Get the build environment batch script::

   cd workspace
   git clone git@github.com:niftools/buildenv.git

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

Install Sphinx and Nose
-----------------------

**Windows** run in buildenv::

   pip install Sphinx --target="%APPDATABLENDERADDONS%\modules"
   pip install nose --target="%APPDATABLENDERADDONS%\modules"

**Ubuntu** run in a terminal::

   sudo apt-get install python3-nose python3-sphinx


**Fedora** run in a terminal::

   sudo yum install python3-nose python3-sphinx

Check Installation
------------------

To verify everything is installed correctly, start blender, open the internal Python console,
and type::

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

#. Install `Eclipse Luna <http://www.eclipse.org/downloads/>`_

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

  2. Under **Work with**, select **--All Available Sites--**.

  3. A large number of plugins will be listed. Select
     **Collaboration >   Eclipse Git Team Provider**
 
  4. Click **Next**, and follow the instructions.
     
  - **Note:** If you experience problems with CLFR/EOF even though you set ``git config --global user.autocrlf true``, 
     
  - Enable the following: Windows -> Preferences -> General -> Compare/Patch -> Ignore WhiteSpaces

* `PyDev <http://pydev.org/>`_
  is an Eclipse plugin targeted at Python development,
  including sytax highlighting and debugging.

  1. Go to: **Help > Install New Software > Add...**

  2. Enter the project update site:
     ``http://pydev.org/updates/``

  3. Select **PyDev**.

  4. Click **Next**, and follow the instructions.

  5. Once installed, you need to configure the
     Python interpreter. Go to **Window > Preferences > PyDev > Interpreters > Python Interpreter** 
     and select **Quick Auto Config**.

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

The Blender nif plugin repo comes with built-in code to connect to a Remote Python Debug Server.
This allows run-time debugging; watching the script execute, variables, function call stack etc.

Launching Blender
`````````````````

Blender should be launched via BuildEnv, using ``start blender``

Setup Eclipse PyDev Debugger
````````````````````````````
Add the Pydev Debug Perspective: **Window > Customise Perspective > Command Groups Availability > Pydev Debug**.

 * Start the Pydev Debug server from the toolbar.

Debugging with PyDev
''''''''''''''''''''

 * Debugging is enabled by default.
 * The debug scripts require Environmental variables defined by the .ini as previous described above.

 ..Note::
   
   Each time PyDev is updated the path defined in the .ini file will need to be updated also.

* This works both from Blender run via ``start blender`` or via the nose test suite.

* When the plugin loads it will attempt to connect the internal server to the eclipses server, it will prompt if failure.

.. note::
   * Executing the script, Eclipse will automatically open the file once it encounters the breakpoint.
   * Remember to run install.bat to overwrite the old addon version.

Happy coding & debugging.
