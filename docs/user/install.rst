Installation
============

.. _user-getblender:

Install Blender
---------------

Windows
~~~~~~~

.. warning::

   The recommended procedure for installing concurrently with the
   old 2.49b version of blender is:

   #. Uninstall all versions of blender that you have installed already
      (2.4x *and* 2.5x versions):

      * Uninstall them via the control panel.

      * Just to make sure,
        search your ``Program Files`` folder for any traces of Blender
        and wipe them out.

   #. Download the 
      `old blender 2.49b .exe installer
      <http://download.blender.org/release/Blender2.49b/blender-2.49b-windows.exe>`_
      and install it **in a non-default folder**, such as
      ``C:\Program Files\Blender Foundation\Blender 2.49b``.

   #. Install the `old blender nif scripts
      <http://sourceforge.net/projects/niftools/files/blender_nif_scripts/2.5.x/>`_.

   #. Install the latest version of blender, as described below.

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

Install and Register the Addon
------------------------------

#. Download the `blender nif plugin .zip release
   <http://sourceforge.net/projects/niftools/files/blender_nif_plugin/>`_.

#. Start blender.

#. Go to: **File > User Preferences > Add-Ons**.

#. Click **Install Addon...** (bottom).

#. Select the blender nif plugin .zip file downloaded earlier.

#. Under **Categories** (left), select **Import-Export**.

#. Tick the empty box next to **Import-Export: NetImmerse/Gambryo nif format**.
   You may have to scroll down a bit first.

#. Close the **Blender User Preferences** window.

#. The nif importer and exporter should now show under
   **File > Import** and **File > Export**.

#. Do: **File > Save User Settings** (unless you enjoy enabling the
   addon every time when blender starts :-) ).

