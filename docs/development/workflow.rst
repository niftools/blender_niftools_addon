Workflow
========

Run Regression Tests
--------------------

To run all tests, run the following in a buildenv (Windows)::

  blender-nosetests.bat

or 

terminal (Fedora)::

  ./blender-nosetests.sh

terminal (Ubuntu)::
	sh blender-nosetests.sh

from within the ``blender_nif_plugin`` folder.
Beware that the output can be rather verbose,
so you may have to scroll quite a bit to see the relevant backtrace.

Each test resides as a python file in the ``blender_nif_plugin/test`` folder.
To run a particular test only, specify the file as an argument; for instance::

  blender-nosetests.bat test/test_cube.py

Actually, all command line arguments of ``nosetests`` apply.
For more details, run::

  blender-nosetests.bat --help

Also see the
`nose manual <http://readthedocs.org/docs/nose/en/latest/usage.html#options>`_.

Generate Documentation
----------------------

Run the following in a buildenv (Windows) or terminal (Fedora)::

  cd blender_nif_plugin/docs
  make html

To view the docs, open ``docs/_build/html/index.html``.
