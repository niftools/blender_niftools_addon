Downloading the Source Code
===========================

.. _developer-setup-sourcecode:

This section will guide new developers through the process of downloading the source code.
We use git as to manage and version our source control.
It is hosted on github, a popular git hosting platform. 


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

Setup SSH Keys
--------------

Follow the instructions at `Github's SSH Page <https://help.github.com/articles/generating-ssh-keys/>`_.

.. note::

   * If you run into errors while starting the ssh-agent or adding the keys to the ssh-agent try running "eval `ssh-agent -s`".


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


Get the Source Code
-------------------

To get the code, run in a terminal (linux) or in git bash (windows)::

   cd ~/workspace
   git clone --recursive git@github.com:<username>/blender_nif_plugin.git
   cd blender_nif_plugin

We use submodules to maintain dependancies.
They are external repositories which can be updated and maintained as standalone projects, but allows us to choose which version to use. 

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

