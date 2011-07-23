Development
===========

Fedora
++++++

Getting Blender
---------------

For Fedora 16 and up, Blender 2.5x is available via yum::

  yum install blender

For Fedora 15, first setup a development environment
(see `http://fedoraproject.org/wiki/How_to_create_an_RPM_package`_)::

  sudo yum groupinstall "Development Tools" -y
  sudo yum install rpmdevtools -y
  rpmdev-setuptree

Then, clone the spec file, install the sources, install the build
dependencies---there may be more than the ones listed below---and kick
off an rpm build::

  git clone git://pkgs.fedoraproject.org/blender
  cd blender
  cp * ~/rpmbuild/SOURCES/
  wget http://download.blender.org/source/blender-2.58a.tar.gz
  mv blender-2.58a.tar.gz ~/rpmbuild/SOURCES/
  cat blender.spec | grep ^BuildRequires | gawk '{ print $2 }' | xargs sudo yum install -y
  rpmbuild -ba blender.spec

Building blender takes a long time. When it is all done, install the rpm::

  sudo yum localinstall ~/rpmbuild/RPMS/x86_64/blender-2.58a-1.fc15.x86_64.rpm

.. warning::

   The package upgrades Blender 2.49b, so if you had it installed
   previously, it will no longer be available. Do::

     sudo yum erase blender
     sudo yum install blender

   to get your old Blender 2.49b back.

Generating Documentation
------------------------

The following instructions work on Fedora 15, with blender installed
in ``~/src/blender25''.

First, install the development version of Sphinx for Python 3.2::

  sudo yum install python3-tools
  easy_install-3.2 --user sphinx==dev

Windows
+++++++

.. todo::

   Write some instructions here.
