**************
Test Framework
**************

.. _development-testframework:

The test framework is a series of tools to automate the verification process of the Blender Niftools Addon that aims
to unify the various levels of testing that should be performed to release the addon:

* Unit
* Functional
* Integration
* Regression
* Performance

For an overview of each level see the :ref:`design section
<development-testframework-design>`

-------------
Prerequisites
-------------

The following environmental variables **must** be set.

We decided not to auto-detect file paths as devs may have many versions installed. This also allows switching between
versions of Blender to run tests against.

~~~~~~~~~~~~
BLENDER_HOME
~~~~~~~~~~~~

Set to the folder the blender.exe installation is contained in, e.g.,

.. code-block:: shell

    BLENDER_HOME=C:/Program Files/Blender Foundation/

or from a terminal (Linux):

.. code-block:: shell

    BLENDER_HOME=~/.blender/

~~~~~~~~~~~~~~~~~~
BLENDER_ADDONS_DIR
~~~~~~~~~~~~~~~~~~

Installs the Blender Nif addon and its dependencies.

Set the location of corresponding Blender addons folder:

.. code-block:: shell

    BLENDER_ADDONS_DIR=%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons

or from a terminal (Linux):

.. code-block:: shell

    BLENDER_ADDONS_DIR=~/.blender/<version>/scripts/addons

-------
Install
-------

To install the addon from a git checkout, run the following:

.. code-block:: shell

   cd blender_niftools_addon/install
   install.bat

or from a terminal (Linux):

.. code-block:: shell

    ./blender_niftools_addon/install
    sh ./install.sh

-------------
Running Tests
-------------

To run all tests, run the following in a buildenv (Windows):

.. code-block:: shell

    blender-nosetests.bat

or from a terminal (Linux):

.. code-block:: shell

    sh ./blender-nosetests.sh

from within the ``blender_niftools_addon/testframework/`` folder.

Each test resides as a python file in the ``blender_niftools_addon/testframework/test/`` folder. To run a particular
test only, specify the file as an argument; for instance

.. code-block:: shell

    blender-nosetests.[bat|sh] test/geometry/trishape/test_geometry.py

Actually, all command line arguments of ``nosetests`` apply. For example, to abort on first failure

.. code-block:: shell

    blender-nosetests.bat -x

For more details, run

.. code-block:: shell

    blender-nosetests.[bat|sh] --help

* The tests will run on the currently installed addon (*not* your checked out version!) so usually ensure you
  re-install after making edits to add-on files.

* Beware that the output can be rather verbose, so you may have to scroll quite a bit to see the relevant backtrace.
  Also, see the `nose manual <http://readthedocs.org/docs/nose/en/latest/usage.html#options>`_.

.. toctree::
   :maxdepth: 1

   design/index
   api/index
   ci_server

------------------
Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
