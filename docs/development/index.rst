Development
===========

The code is maintained with git. If you are not yet familiar with git,
read `progit <http://progit.org/book/>`_.

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

As preparation for what follows next, read the remaining `github help
pages <http://help.github.com/>`_, particularly the beginner's
guides. Next are platform specific instructions---we will cover Fedora
and Windows.

Fedora
++++++

Get the code
------------

::

  sudo yum install git
  mkdir ~/workspace
  cd ~/workspace
  git clone git@github.com:<username>/blender_nif_scripts.git

Get Python 3
------------

::

  sudo yum install python3 python3-tools

Get Blender
-----------

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
  wget http://download.blender.org/source/blender-2.59.tar.gz
  mv blender-2.59.tar.gz ~/rpmbuild/SOURCES/
  cat blender.spec | grep ^BuildRequires | gawk '{ print $2 }' | xargs sudo yum install -y
  rpmbuild -ba blender.spec

Building blender takes a long time. When the build is finished,
install the rpm::

  sudo yum localinstall ~/rpmbuild/RPMS/x86_64/blender-2.59-1.fc15.x86_64.rpm

.. warning::

   The package upgrades Blender 2.49b, so if you had it installed
   previously, it will no longer be available. Do::

     sudo yum erase blender
     sudo yum install blender

   to get your old Blender 2.49b back.

Getting PyFFI
-------------

The blender nif scripts require pyffi. You will need to install a
version of pyffi that works with blender::

  git clone --recursive git://github.com/amorilia/pyffi.git
  cd pyffi
  python3 setup.py install --user

Generating Documentation
------------------------

First, install the development version of Sphinx for Python 3.2::

  sudo yum install python3-tools
  easy_install-3.2 --user sphinx==dev

Then simply do::

  cd docs
  make html

from within your blender nif scripts git checkout. The sphinx builder
runs from within blender---the blender window will show briefly while
the documentation is generated.

Get Eclipse
-----------

This is entirely optional.

For editing the code, `eclipse <http://www.eclipse.org/>`_ provides a
bloated yet convenient environment. First, install eclipse and its
Python and git plugins::

  sudo yum install eclipse-pydev eclipse-egit

Start eclipse with::

  eclipse

Eclipse will ask you for your workspace folder---if you followed the
instructions above and cloned the code into
``~/workspace/blender_nif_scripts``, then the default
``/home/<username>/workspace`` will do the trick. If not, pick the
folder in which the ``blender_nif_scripts`` clone resides.

At the Welcome window, click **Workbench** on the top right.

Configure PyDev
~~~~~~~~~~~~~~~

1. Go to: **Window > Preferences > PyDev > Interpreter - Python > New > Browse**.

2. Choose ``/usr/bin/python3``.

3. Confirm your selection, and accept the defaults: **Ok > Ok > Ok**.

Import Project
~~~~~~~~~~~~~~

1. Go to: **File > Import > General > Existing Projects into Workspace > Next > Browse**.

2. Choose the ``blender_nif_scripts`` folder and select **Ok > Finish**.

3. If you want to use git from within eclipse, right click the project
   in the Project Explorer, and choose **Team > Share Project > Git**.
   Enable **Use or create Repository in parent folder of project**,
   and click **Finish**.

Windows
+++++++

Installation:
Create a directory to be used as your coding directory. E.g ../Desktop/coding/Niftools

Blender:
	Download the latest supported `version <http://www.blender.org/download/get-blender/>`_
	
	Follow the installer instructions, 
	If you wish to install concurrently with a version of 2.49 install to 
	- C:\Program Files\Blender Foundation\Blender2.x

Python 3.2:
	Download the latest supported production `version <http://www.python.org/download/releases/`_
	
	Install python as per the installers instructions to the default location.

Git Bash:
	This is used to setup local code repositories and pull remote versions. 
	Download the latest `version <http://code.google.com/p/msysgit/downloads/list>`_ and follow the installer 
	- 
	
	Although you only need to pull the repos, if you want to push patches
	it is advised to create a github account. Even if you do not wish to you 
	should read through the ` setup guide <http://help.github.com/win-set-up-git/>`_

Eclipse:
	Eclipse is was chosen as the IDE due to its flexible plug-ins for repo management, 
	python scripting and hooks into Blenders debugging console. 
	Install `Eclipse Indigo <http://www.eclipse.org/downloads/packages/eclipse-classic-37/indigor>`_ for windows platform.

Eclipse Plug-ins:
	Under Help->Install New Software install:

	EGit Subversion:
	Egit is an Eclipse module to perform git action from within Eclipse.
	Location - http://download.eclipse.org/egit/updates/
	
	Pydev:
	Pydev is an Eclipse module targeted at Python development, including sytax highlighting and debugging
	Location - http://pydev.org/updates/

PYFFI:
::TODO::
	Amorilia, suggestions for best way to install on win platform.
	Installer or copy scripts to Blender directory.	

Downloading Blender Scripts:
	Git bash
	::cd /Desktop/coding/Niftools/
	
	remote location if you have forked the repo
	::git clone --recursive git@github.com:yourusername/blender_nif_scripts.git
	Main Blender nifscripts repo
	::git clone --recursive git://github.com/amorilia/blender_nif_scripts.git
	or
	::git clone --recursive git://github.com/neomonkeus/blender_nif_scripts.git
	
	
Development
+++++

Once you have cloned this Repo to your local, copy all files in debug files to ../Blender Foundation/Blender
Run docs/refresh_python_api.bat to generate the current the current API 
pydev_debug & Run.py will hook up Eclipse's Pydev Debug to Blender's debugger.

Import local repo into Eclipse using Team->Git as an existing project.
Link the external Api to the project:
Project->Properties->Pydev - PYTHONPATH->external libraries->
../Blender/docs/python_api/pypredef/

Start the Pydev debug server and switch to debug mode.
Open the .blend file, then open the run.py in the text editor.
Replace the strings:
1: python debugger location.
2: main execution file location.

Start the Pydev debug server and switch to debug mode.
Open the .blend file, then open the run.py in the text editor.
