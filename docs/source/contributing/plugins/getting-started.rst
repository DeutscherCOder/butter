Getting Started with Python Plugins
===================================

This article provides a step-by-step guide on how to write a simple Python plugin for Clutter.

Create a python file, called ``myplugin.py`` for example, and add the following contents:

.. code-block:: python

   import clutter

   class MyClutterPlugin(clutter.ClutterPlugin):
       name = "My Plugin"
       description = "This plugin does awesome things!"
       version = "1.0"
       author = "1337 h4x0r"

       def setupPlugin(self):
           pass

       def setupInterface(self, main):
           pass

       def terminate(self):
           pass

   def create_clutter_plugin():
       return MyClutterPlugin()

This is the most basic code that makes up a plugin.
Python plugins in Clutter are regular Python modules that are imported automatically on startup.
In order to load the plugin, Clutter will call the function ``create_clutter_plugin()`` located
in the root of the module and expects it to return an instance of ``clutter.ClutterPlugin``.
Normally, you shouldn't have to do anything else in this function.

.. note::
   The Clutter API is exposed through the ``clutter`` module.
   This consists mostly of direct bindings of the original C++ classes, generated with Shiboken6.
   For more detail about this API, see the Clutter C++ code or :ref:`api`.

The ``ClutterPlugin`` subclass contains some meta-info and two callback methods:

* ``setupPlugin()`` is called right after the plugin is loaded and can be used to initialize the plugin itself.
* ``setupInterface()`` is called with the instance of MainWindow as an argument and should create and register any UI components.
* ``terminate()`` is called on shutdown and should clean up any resources used by the plugin.

Copy this file into the ``python`` subdirectory located under the plugins directory of Clutter and start the application.
You should see an entry for your plugin in the list under Edit -> Preferences -> Plugins.
Here, the absolute path to the plugins directory is shown too if you are unsure where to put your plugin:

.. image:: preferences-plugins.png

.. note::
   As mentioned, plugins are Python modules. This means, instead of only a single .py file, you can also
   use a directory containing multiple python files and an ``__init__.py`` file that defines or imports the
   ``create_clutter_plugin()`` function.

.. note::
   If you are working on a Unix-like system, instead of copying, you can also symlink your plugin into the plugins
   directory, which lets you store the plugin somewhere else without having to copy the files over and over again.


Creating a Widget
-----------------

Next, we are going to add a simple dock widget. Extend the code as follows:

.. code-block:: python

   import clutter

   from PySide6.QtWidgets import QAction, QLabel

   class MyDockWidget(clutter.ClutterDockWidget):
       def __init__(self, parent, action):
           super(MyDockWidget, self).__init__(parent, action)
           self.setObjectName("MyDockWidget")
           self.setWindowTitle("My cool DockWidget")

           label = QLabel(self)
           self.setWidget(label)
           label.setText("Hello World")

   class MyClutterPlugin(clutter.ClutterPlugin):
       # ...

       def setupInterface(self, main):
           action = QAction("My Plugin", main)
           action.setCheckable(True)
           widget = MyDockWidget(main, action)
           main.addPluginDockWidget(widget, action)

   # ...

We are subclassing ``clutter.ClutterDockWidget``, which is the base class for all dock widgets in Clutter,
and adding a label to it.

.. note::
   You can access the whole Qt6 API from Python, which is exposed by PySide6. For more information about this, refer to the
   Documentation of `Qt <https://doc.qt.io/qt-6/reference-overview.html>`_ and `PySide6 <https://wiki.qt.io/Qt_for_Python>`_.

.. note::
   Main clutter packages are now using QT6, but Qt5 builds are still provided for compatibilty with older OS versions. If you
   want your plugin to support both, Qt usage process is a bit more complicated.

In our ``setupInterface()`` method, we create an instance of our dock widget and an action to be
added to the menu for showing and hiding the widget.
MainWindow provides a helper method called ``addPluginDockWidget()`` to easily register these.

When running Clutter now, you should see the widget:

.. image:: mydockwidget.png

... as well as the action:

.. image:: mydockwidget-action.png


Fetching Data
-------------

Next, we want to show some actual data from the binary in our widget.
As an example, we will display the instruction and instruction size at the current position.
Extend the code as follows:

.. code-block:: python

   # ...

   class MyDockWidget(clutter.ClutterDockWidget):
       def __init__(self, parent, action):
           # ...

           label = QLabel(self)
           self.setWidget(label)

           disasm = clutter.cmd("pd 1").strip()

           instruction = clutter.cmdj("pdj 1")
           size = instruction[0]["size"]

           label.setText("Current disassembly:\n{}\nwith size {}".format(disasm, size))

   # ...

We can access the data by calling Rizin commands and utilizing their output.
This is done by using the two functions ``cmd()`` and ``cmdj()``, which behave just as they
do in `rz-pipe <https://book.rizin.re/scripting/rz-pipe.html>`_.

Many commands in Rizin can be suffixed with a ``j`` to return JSON output.
``cmdj()`` will automatically deserialize the JSON into python dicts and lists, so the
information can be easily accessed.

.. warning::
   When fetching data that is not meant to be used only as readable text, **always** use the JSON variant of a command!
   Regular command output is not meant to be parsed and is subject to change at any time, which will break your code.

In our case, we use the two commands ``pd`` (Print Disassembly) and ``pdj`` (Print Disassembly as JSON)
with a parameter of 1 to fetch a single line of disassembly.

.. note::
   To try out commands, you can use the Console widget in Clutter. Almost all commands support a ``?`` suffix, like in
   ``pd?``, to show help and available sub-commands.
   To get a general overview, enter a single ``?``.

The result will look like the following:

.. image:: disasm-static.png

Of course, since we only fetch the info once during the creation of the widget, the content never updates.
We are going to change that in the next section.


Reacting to Events
------------------

We want to update the content of our widget on every seek.
This can be done like the following:

.. code-block:: python

   # ...

   from PySide6.QtCore import QObject, SIGNAL

   # ...

   class MyDockWidget(clutter.ClutterDockWidget):
       def __init__(self, parent, action):
           # ...

           self._label = QLabel(self)
           self.setWidget(self._label)

           QObject.connect(clutter.core(), SIGNAL("seekChanged(RVA)"), self.update_contents)

       def update_contents(self):
           disasm = clutter.cmd("pd 1").strip()

           instruction = clutter.cmdj("pdj 1")
           size = instruction[0]["size"]

           self._label.setText("Current disassembly:\n{}\nwith size {}".format(disasm, size))


First, we move the update code to a separate method.
Then we call ``clutter.core()``, which returns the global instance of ``ClutterCore``.
This class provides the Qt signal ``seekChanged(RVA)``, which is emitted every time the current seek changes.
We can simply connect this signal to our method and our widget will update as we expect it to:

.. image:: disasm-dynamic.png

For more information about Qt signals and slots, refer to `<https://doc.qt.io/qt-6/signalsandslots.html>`_.

Full Code
---------

.. code-block:: python

   import clutter

   from PySide6.QtCore import QObject, SIGNAL
   from PySide6.QtWidgets import QLabel
   from PySide6.QtGui import QAction

   class MyDockWidget(clutter.ClutterDockWidget):
       def __init__(self, parent, action):
           super(MyDockWidget, self).__init__(parent, action)
           self.setObjectName("MyDockWidget")
           self.setWindowTitle("My cool DockWidget")

           self._label = QLabel(self)
           self.setWidget(self._label)

           QObject.connect(clutter.core(), SIGNAL("seekChanged(RVA)"), self.update_contents)

       def update_contents(self):
           disasm = clutter.cmd("pd 1").strip()

           instruction = clutter.cmdj("pdj 1")
           size = instruction[0]["size"]

           self._label.setText("Current disassembly:\n{}\nwith size {}".format(disasm, size))


   class MyClutterPlugin(clutter.ClutterPlugin):
       name = "My Plugin"
       description = "This plugin does awesome things!"
       version = "1.0"
       author = "1337 h4x0r"

       def setupPlugin(self):
           pass

       def setupInterface(self, main):
           action = QAction("My Plugin", main)
           action.setCheckable(True)
           widget = MyDockWidget(main, action)
           main.addPluginDockWidget(widget, action)

       def terminate(self):
           pass

   def create_clutter_plugin():
       return MyClutterPlugin()
