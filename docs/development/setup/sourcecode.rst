Downloading the Source Code
===========================

.. _development-setup-sourcecode:

This section will guide new developers through the process of downloading the source code.
We use git as to manage and version our source control.
It is hosted on GitHub, a popular git hosting platform. 


Install Git
-----------

The code is maintained with git. If you are not yet familiar with git, read `progit <http://progit.org/book/>`_.

**Windows**

We use git bash.
Download `git bash <https://git-scm.com/downloads>`_ installer and follow the instructions.

**Fedora**::

   sudo yum install git

**Ubuntu**::

   sudo apt-get install git

Auto CLRF
`````````

* We need to ensure consistency of end-of-file(EOF) markers between Unix & Windows platforms.
* Locally it will keep your platform specifics EOF, but when you go to push it will update files as necessary
* This avoids unnecessary commits when your environment is different to the remote.
* Without this option, Git will see the different markers and think that the whole file has been edited.
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
clone the code on GitHub.

#. If you do not have one yet, `create a GitHub account <https://github.com/signup/free>`_.

#. Set up your `git environment <http://help.github.com/set-up-git-redirect>`_.

#. `Log in <https://github.com/login>`_ on GitHub.

#. Visit the `Blender Nif Plugin mothership repository <https://github.com/niftools/blender_niftools_addon>`_.

#. Click **Fork** (top right corner).

Be sure to read the remaining `GitHub help pages <http://help.github.com/>`_, particularly the beginner's guides.


Get the Source Code
-------------------

To get the code, run in a terminal (linux) or in git bash (windows)::

   cd ~/workspace
   git clone --recursive git@github.com:<username>/blender_niftools_addon.git
   cd blender_niftools_addon

We use submodules to maintain external dependencies.
This allows us to update to a version of the dependency independently of the corresponding project's release cycle.

Fetching the submodules::
   
   $ git submodule update --init
   
If you get the following error::

   fatal: Needed a single revision 
   Unable to find current revision in submodule path ’pyffi’

Run::
   
   $ rm -rf pyffi   
   $ git submodule update --init

Optional remote tracking of other developers::

   git remote add <developer> git://github.com/<developer>/blender_niftools_addon.git
