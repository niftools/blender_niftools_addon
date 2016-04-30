Test Framework
==============

.. _development-testframework:

The test framework is a series of tools to automate the verification process of the Blender Nif Plugin
It aims to unify the various levels of testing that should be performed to release the plugin

 * Unit
 * Functional
 * Integration
 * Regression
 * Performance

For an overview of each level see the :ref: `design section <development-testframework-design>`

Install
-------

To install the plugin from a git checkout,
run the following in a buildenv (Windows)::
   
   cd blender_nif_plugin/install
   install.bat

or from a terminal (Linux | Ubuntu)::
   
   ./blender_nif_plugin/install
   sh ./install.sh
   
Running Tests
-------------

To run all tests, run the following in a buildenv (Windows)::

  blender-nosetests.bat

or from a terminal (Linux | Ubuntu)::

  sh ./blender-nosetests.sh

from within the ``blender_nif_plugin/testframework/`` folder.

Each test resides as a python file in the ``blender_nif_plugin/testframework/test/`` folder.
To run a particular test only, specify the file as an argument; for instance::

  blender-nosetests.bat test/geometry/trishape/test_geometry.py

Actually, all command line arguments of ``nosetests`` apply.
For example, to abort on first failure::

  blender-nosetests.bat -x

For more details, run::

  blender-nosetests.bat --help

* The tests will run on the currently installed plugin (*not* your checked out version!) so usually ensure you re-install after making edits to add-on files.
* Beware that the output can be rather verbose, so you may have to scroll quite a bit to see the relevant backtrace.

Also see the
`nose manual <http://readthedocs.org/docs/nose/en/latest/usage.html#options>`_.

.. toctree::
   :maxdepth: 1
   
   design/index
   api/index
   ci_server
   
Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
