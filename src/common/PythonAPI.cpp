#include "PythonAPI.h"

#include "ClutterConfig.h"
#include "core/Clutter.h"

#include <QFile>

PyObject *api_version(PyObject *self, PyObject *null)
{
    Q_UNUSED(self)
    Q_UNUSED(null)
    return PyUnicode_FromString(CLUTTER_VERSION_FULL);
}

PyObject *api_cmd(PyObject *self, PyObject *args)
{
    Q_UNUSED(self);
    char *command;
    char *result = (char *)"";
    QString cmdRes;
    QByteArray cmdBytes;
    if (PyArg_ParseTuple(args, "s:command", &command)) {
        cmdRes = Core()->cmd(command);
        cmdBytes = cmdRes.toLocal8Bit();
        result = cmdBytes.data();
    }
    return PyUnicode_FromString(result);
}

PyObject *api_refresh(PyObject *self, PyObject *args)
{
    Q_UNUSED(self);
    Q_UNUSED(args);
    Core()->triggerRefreshAll();
    Py_RETURN_NONE;
}

PyObject *api_message(PyObject *self, PyObject *args, PyObject *kwargs)
{
    Q_UNUSED(self);
    char *message;
    int debug = 0;
    static const char *kwlist[] = { "", "debug", NULL };
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "s|i", const_cast<char **>(kwlist), &message,
                                     &debug)) {
        return NULL;
    }
    Core()->message(QString(message), debug);
    Py_RETURN_NONE;
}

PyMethodDef ClutterMethods[] = {
    { "version", api_version, METH_NOARGS, "Returns Clutter current version" },
    { "cmd", api_cmd, METH_VARARGS, "Execute a command inside Clutter" },
    { "refresh", api_refresh, METH_NOARGS, "Refresh Clutter widgets" },
    { "message", (PyCFunction)(void *)/* don't remove this double cast! */ api_message,
      METH_VARARGS | METH_KEYWORDS, "Print message" },
    { NULL, NULL, 0, NULL }
};

PyModuleDef ClutterModule = {
    PyModuleDef_HEAD_INIT, "_clutter", NULL, -1, ClutterMethods, NULL, NULL, NULL, NULL
};

PyObject *PyInit_api()
{
    return PyModule_Create(&ClutterModule);
}
