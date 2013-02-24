Workflow
========

Install
-------

To install the plugin from a git checkout,
run the following in a buildenv (Windows)::
   
   cd blender_nif_plugin/install
   install.bat

or from a terminal (Linux | Ubuntu)::
   
   ./blender_nif_plugin/install
   sh ./install.sh
   

Run Regression Tests
--------------------

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

Generate Documentation
----------------------

Run the following in a buildenv (Windows) or terminal (Fedora)::

  make html

from within the ``blender_nif_plugin/docs`` folder.
The generated API documentation
will correspond to the currently installed plugin
(*not* your checked out version!)
so usually you would install it first.

To view the docs, open ``docs/_build/html/index.html``.
