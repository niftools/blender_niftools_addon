===================================
Interactive Development Environment
===================================

.. _development-design-setup-ide:

Developers are open to use their own IDE of preference, but the repo is configured towards Jetbrains IDEs such PyCharm or IntelliJ Ultimate.
This IDE allows us to maintain a unified workflow for general file manipulation, repo management,
python scripting, and hooks into Blender's debugging server.

---------------
Install PyCharm
---------------

**Windows**

#. Download `PyCharm <https://www.jetbrains.com/pycharm/download>`_

**Fedora**, simply run::

    sudo yum install eclipse eclipse-egit eclipse-pydev

**Ubuntu**, simply run::

    sudo snap install [pycharm-professional|pycharm-community] --classic

When starting pycharm, Open the workspace folder.
If you followed the instructions, you should have cloned the code into ``/home/<username>/workspace``
PyCharm will automatically recognise this as a Git repo.

---------
Debugging
---------

The Blender Niftools Addon code comes with built-in pydev hook to allow connection by a Remote Python Debug Server.
This allows run-time debugging; watching the script execute, evaluate variables, function call stack etc.

********
Debugger
********

The following ENV variable is used to pick up the location of `pydevd` which is installed via the install_deps.sh script.
    export PYDEVDEBUG="${BLENDER_ADDONS_DIR}"

In the IDE, create a new configuration of type `Python Debug Server`, update the port as per the util_debug.py settings.
This can then be launched and should wait for the debug thread to call back into the server.::

    Starting debug server at port 1234
    Use the following code to connect to the debugger:
    import pydevd_pycharm
    pydevd_pycharm.settrace('localhost', port=1234, stdoutToServer=True, stderrToServer=True)
    Waiting for process connection...
    Connected to pydev debugger (build 201.6668.115)

Launching `Blender` via Terminal, it will suspend once it hits the trace call executes ::

    settrace('localhost', port=port, stdoutToServer=True, stderrToServer=True, suspend=True)

The debugger may as you to provide a source path so that it can map the code being executed to the code in the IDE.
This allows you to put breakpoints in your code directly.

Happy coding & debugging.
