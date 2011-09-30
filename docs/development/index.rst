Development
===========

The code is maintained with git. If you are not yet familiar with git,
read `progit <http://progit.org/book/>`_.

.. _create-github-account:

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

.. warning::

    The following instructions are work in progress.

First, create a directory to be used as your coding directory, such as
``C:\Users\<username>\workspace``.

Get Blender
-----------

`Download <http://www.blender.org/download/get-blender/>`_
the latest supported version, and
follow the installer instructions, 

If you wish to install concurrently with a version of 2.49 install to
another folder, such as
``C:\Program Files\Blender Foundation\Blender2.x``.

Get Git Bash
------------

This is used to setup local code repositories and pull remote versions. 
Download `msysgit <http://code.google.com/p/msysgit/downloads/list>`_ and follow the installer instructions.

Although you only need to pull the repos, if you want to push patches
it is advised to :ref:`create a github account <create-github-account>`.

Get Python 3.2
--------------

This is only needed if you wish to

* use Eclipse as IDE, or

* generate the documentation.

`Download <http://www.python.org/download/releases/3.2.2/>`_ the
installer appropriate for your platform, and
follow the instructions. The default location should work fine.

Copy and paste `buildenv-python.bat <https://gist.github.com/1254859>`_
into a new text file called ``buildenv-python.bat`` in your ``workspace`` folder.
right-click on the file, and select **Send to > Desktop (create shortcut)**.

Now right-click this newly created shortcut, and change **Target** into::

  %comspec% /k C:\Users\<username>\workspace\buildenv-python.bat C:\Python32 msvc2008 64 workspace

(on 32 bit systems, type ``32`` instead of ``64``).

For ease of installing various developer dependencies,
save `distribute_setup.py
<http://python-distribute.org/distribute_setup.py>`_ 
in your ``workspace`` folder, and execute it:
double click on the Python build environment shortcut you just created,
and type::

  python distribute_setup.py

Next, we install pip::

  easy_install pip

Then, we install Sphinx and all of its dependencies::

  pip install Sphinx==dev

Now, copy everything from ``C:\Python32\Lib\site-packages`` to 

Start the git bash, and type::

  cd workspace
  git clone --recursive git://github.com/amorilia/pyffi.git
  git clone --recursive git@github.com:<username>/blender_nif_scripts.git
  cd blender_nif_scripts
  git remote add amorilia git://github.com/amorilia/blender_nif_scripts.git
  git remote add neomonkeus git://github.com/neomonkeus/blender_nif_scripts.git

Back in your Python build environment, type::

  cd pyffi
  python setup.py install

Finally, copy your entire ``C:\Python32\Lib\site-packages`` folder to
``C:\Program Files\Blender Foundation\Blender\2.59\python\lib\site-packages``.
To check that everything is installed correctly, start Blender, open a Python console,
and type::

  import site
  import pyffi
  import sphinx

You should not get any import errors.

Generating Documentation
------------------------

Start your Python build environment, and simply do::

  cd blender_nif_scripts
  cd docs
  make html

The sphinx builder
runs from within blender---the blender window will show briefly while
the documentation is generated.

.. todo::

   At the moment, we are still using Python. Script needs updating to eventually recognize Blender.

Eclipse
-------

Eclipse is chosen as the IDE due to its flexible plug-ins for repo management, 
python scripting and hooks into Blenders debugging console. 

First, install the `Java Runtime Environment <http://java.com/download>`_.
Make sure you have the right version---on 64 bit platforms, it is safest
to pick right file via `manual download <http://java.com/en/download/manual.jsp>`_.

Next, install `Eclipse Classic <http://www.eclipse.org/downloads/>`_ for the windows platform.
Just unzip the file, and put it somewhere convenient, such as under ``C:\eclipse``.
If you want to create a shortcut from your desktop, right-click ``C:\eclipse\eclipse.exe``
and select **Send to > Desktop (create shortcut)**.

You should also install a few plugins. Under **Help > Install New Software**,
install:

EGit
~~~~

Egit is an Eclipse module to perform git action from within Eclipse.
http://download.eclipse.org/egit/updates/
	
Pydev
~~~~~

Pydev is an Eclipse module targeted at Python development, including sytax highlighting and debugging
http://pydev.org/updates/

Eclipse: Command line completion
--------------------------------

.. todo::

   Update for actual location
   of command line completion code.

Once you have cloned this Repo to your local, copy the following to the Blender directory::

    ./docs/python_api/
    ./docs/refresh_python_api.bat
    run.py
    pydev_debug.py

Run docs/refresh_python_api.bat to generate an updated API 
pydev_debug.py & run.py will be used to hook Eclipse's Pydev Debug to Blender's debugger.	
	
Eclipse: Import Project
-----------------------

Import local repo into Eclipse using **Team > Git** as an existing project.

Link the external Blender Python_Api to the project:
**Project > Properties > Pydev - PYTHONPATH > external libraries > ../Blender/docs/python_api/pypredef/**

Limitations: Types declarations should be fully qualified type before auto-completion kicks in
e.g obj = bpy.types.object, obj = bpy.context.active_object
Auto-completion should now work for the majority of the API.
Hovering over a variable will hot-link to the generated documentation.

Eclipse: Debugging
------------------

Add the Pydev Debug: Customise Perspective -> Pydev Debug. 
Always start the Pydev debug server first otherwise blender will crash later.	

Open the ``test/blend/debug.blend`` file 

Open ``run.py`` in the scripting text editor.

Replace the strings:

1. python debugger location.

2. main execution file location.

Run the script; blender will appear to hang but this is as the Debugger has hit the trace() call

In Eclipse switch to debug mode and begin scripting.
