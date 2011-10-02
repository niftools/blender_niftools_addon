User Documentation
==================

.. warning::

   User documentation is incomplete.

.. todo::

   We need to split this into different documents:

   * installation (more or less done, see below),
   * basic tutorial,
   * list of all features
     (it would be a good habit to document every feature we have!)
     and quick instructions for how to use each of them.
   * license,
   * changelog,
   * anything else?

.. _user-getblender:

Install Blender
---------------

Windows
~~~~~~~

.. warning::

   The recommended procedure for installing concurrently with the
   old 2.49b version of blender is:

   1. Uninstall all versions of blender that you have installed already
      (2.4x *and* 2.5x versions):

      * Uninstall them via the control panel.

      * Just to make sure,
        search your ``Program Files`` folder for any traces of Blender
        and wipe them out.

   2. Download the 
      `old blender 2.49b .exe installer
      <http://download.blender.org/release/Blender2.49b/blender-2.49b-windows.exe>`_
      and install it **in a non-default folder**, such as
      ``C:\Program Files\Blender Foundation\Blender 2.49b``.

   3. Install the `old blender nif scripts
      <http://sourceforge.net/projects/niftools/files/blender_nif_scripts/2.5.x/>`_.

   4. Install the latest version of blender, as described below.

Download the
`blender .exe installer <http://www.blender.org/download/get-blender/>`_
for your platform (32-bit or 64-bit; if unsure, pick the 32-bit version)
and follow the instructions.

Fedora
~~~~~~

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

Install PyFFI
-------------

.. warning::

   This section is a stub, pyffi for py3k isn't released yet.

1. Download the `pyffi .exe release
   <http://sourceforge.net/projects/pyffi/files/pyffi-py3k/>`_.

2. Run the installer and follow the instructions.

Install Blender Nif Scripts
---------------------------

.. warning::

   This section is a stub, the scripts aren't released yet.

Windows
~~~~~~~

1. Download the `blender nif scripts .exe release
   <http://sourceforge.net/projects/niftools/files/blender_nif_scripts/>`_.

2. Run the installer and follow the instructions.

Fedora
~~~~~~

1. Download the `blender nif scripts .zip release
   <http://sourceforge.net/projects/niftools/files/blender_nif_scripts/>`_
   and unzip it somewhere.

2. Run the ``install.sh`` script.

Register the Addon
------------------

1. Start blender.

2. Go to: **File > User Preferences > Add-Ons**.

3. Under **Categories** (left), select **Import-Export**.

4. Tick the empty box next to **Import-Export: NetImmerse/Gambryo nif format**.
   You may have to scroll down a bit first.

5. Close the **Blender User Preferences** window.

6. The nif importer and exporter should now show under
   **File > Import** and **File > Export**.

7. Do: **File > Save User Settings** (unless you enjoy enabling the
   addon every time when blender starts :-) ).

Using the Scripts
-----------------

The
`quick-start guide <http://niftools.sourceforge.net/wiki/Blender/Quick_Start>`_
describes how to prepare your textures and how you can use the scripts.
The guide also lists the limitations of the scripts, known issues, and workarounds for some issues.

.. todo::

   Port the quick start guide to the documentation, and give a pointer
   to the generated Sphinx docs.

Support
-------

* `wiki <http://niftools.sourceforge.net/wiki/Blender>`_
* `forum <http://niftools.sourceforge.net/forum>`_
* `report a bug <http://sourceforge.net/tracker/?group_id=149157>`_
  (please include the .blend or .nif that caused the error and a brief description
  of how to reproduce the error)
