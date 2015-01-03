Interactive Development Environment
===================================

The `Eclipse <http://www.eclipse.org/>`_ IDE allows us maintain a unified workflow for general file manipulation,
repo management, python scripting, and hooks into Blender's debugging server.


Install Eclipse
---------------

#. First install the `Java Runtime Environment <http://java.com/download>`_.

* Make sure you have the right version---on 64 bit platforms, it is safest to pick right file via `manual download <http://java.com/en/download/manual.jsp>`_.

**Windows**

#. Install `Eclipse Luna <http://www.eclipse.org/downloads/>`_

#. Unzip the file under ``<workspace>\bin\eclipse``.

* If you want to create a shortcut from your desktop, right-click ``<workspace>\bin\eclipse\eclipse.exe``
  and select **Send to > Desktop (create shortcut)**.

**Fedora**, simply run::

   sudo yum install eclipse eclipse-egit eclipse-pydev

**Ubuntu**, simply run::

   sudo apt-get install eclipse

When starting eclipse, you are asked for your workspace folder. If you followed the
instructions and cloned the code into ``~/workspace/blender_nif_plugin``,
then the default ``/home/<username>/workspace`` will do the trick.

At the Welcome window, click **Workbench** on the top right.


Eclipse Plugins
---------------

You should also install a few plugins.

* `EGit <http://eclipse.org/egit/>`_
  is an Eclipse plugin to perform git actions from within Eclipse.

  1. Go to: **Help > Install New Software > Add...**

  2. Under **Work with**, select **--All Available Sites--**.

  3. A large number of plugins will be listed. Select
     **Collaboration >   Eclipse Git Team Provider**
 
  4. Click **Next**, and follow the instructions.
     
  - **Note:** If you experience problems with CLFR/EOF even though you set ``git config --global user.autocrlf true``, 
     
  - Enable the following: Windows -> Preferences -> General -> Compare/Patch -> Ignore WhiteSpaces

* `PyDev <http://pydev.org/>`_
  is an Eclipse plugin targeted at Python development,
  including sytax highlighting and debugging.

  1. Go to: **Help > Install New Software > Add...**

  2. Enter the project update site:
     ``http://pydev.org/updates/``

  3. Select **PyDev**.

  4. Click **Next**, and follow the instructions.

  5. Once installed, you need to configure the
     Python interpreter. Go to **Window > Preferences > PyDev > Interpreters > Python Interpreter** 
     and select **Quick Auto Config**.

  6. Finally, you may wish to configure the eclipse editor for
     UTF-8 encoding, which is the default encoding used
     for Python code. Go to
     **Window > Preferences > General > Workspace**.
     Under **Text file encoding**, choose **Other**,
     and select **UTF-8** from the list.

* Documentation is written in `reStructuredText
  <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`_.
  If you want syntax highlighting for reST,
  install the `ReST Editor plugin <http://resteditor.sourceforge.net/>`_:

  1. Go to: **Help > Install New Software > Add...**

  2. Enter the project update site:
     ``http://resteditor.sourceforge.net/eclipse``

  3. Under the ReST Editor plugin tree,
     select the ReST Editor plugin,
     and unselect the Eclipse Color Theme mapper plugin.

  4. Click **Next**, and follow the instructions.

Import Projects Into Eclipse
----------------------------

1. Make sure that the plugin's source resides in the ``blender_nif_plugin``
   folder under your workspace folder.

2. Go to: **File > Import > General > Existing Projects into Workspace**.
   Select your workspace folder as root directory, and click **Finish**.

3. For each project that you manage with Git,
   right-click on its name in the Project Explorer,
   select **Team > Share Project > Git**, and click **Next**.
   Leave **Use or create repository in parent folder of project** enabled,
   and click **Finish**.

Eclipse Debugging
-----------------

The Blender nif plugin repo comes with built-in code to connect to a Remote Python Debug Server.
This allows run-time debugging; watching the script execute, variables, function call stack etc.

Launching Blender
`````````````````

Blender should be launched via BuildEnv, using ``start blender``

Setup Eclipse PyDev Debugger
````````````````````````````
Add the Pydev Debug Perspective: **Window > Customise Perspective > Command Groups Availability > Pydev Debug**.

 * Start the Pydev Debug server from the toolbar.

Debugging with PyDev
''''''''''''''''''''

 * Debugging is enabled by default.
 * The debug scripts require Environmental variables defined by the .ini as previous described above.

 ..Note::
   
   Each time PyDev is updated the path defined in the .ini file will need to be updated also.

* This works both from Blender run via ``start blender`` or via the nose test suite.

* When the plugin loads it will attempt to connect the internal server to the eclipses server, it will prompt if failure.

.. note::
   * Breakpoints shoudl be put on the installed files, not the files in the workspace
   * Executing the script, Eclipse will automatically open the file once it encounters the breakpoint.
   * Remember to run install.bat to overwrite the old addon version.

Happy coding & debugging.
