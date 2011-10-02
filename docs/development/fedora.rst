Fedora
======

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

See :ref:`user docs <user-getblender-fedora>`.

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

from within your blender nif scripts git checkout. View the docs with::

  firefox _build/html/index.html &

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
