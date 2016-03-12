Building Blender from Source
============================

.. _development-setup-buildblender:

As a developer, there are a number of advantages that come from building from source.
 * Avoid having to wait for bug fixes from full releases
 * Building the latest version to test compatability early
 * Testing new features and how we can integrate with them
 * Blender can be built as a python module, which can improve IDE integration.

The Blender code repo is also managed by git, allowing ease of integration into our workflow.
There are some additional prerequisite utilities that need to be installed first.


Windows
-------

.. note::
  TODO

Fedora
------

.. warning:: Needs verification

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