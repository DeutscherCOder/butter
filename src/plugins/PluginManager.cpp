#include <cassert>

// clang-format off
#ifdef CLUTTER_ENABLE_PYTHON_BINDINGS
#    include <Python.h>
#    include <clutterbindings_python.h>
#    include "PythonManager.h"
#endif
// clang-format on

#include "ClutterConfig.h"
#include "ClutterPlugin.h"
#include "PluginManager.h"
#include "common/Helpers.h"
#include "common/ResourcePaths.h"

#include <QCoreApplication>
#include <QDebug>
#include <QDir>
#include <QPluginLoader>
#include <QStandardPaths>

Q_GLOBAL_STATIC(PluginManager, uniqueInstance)

PluginManager *PluginManager::getInstance()
{
    return uniqueInstance;
}

PluginManager::PluginManager() {}

PluginManager::~PluginManager() {}

void PluginManager::loadPlugins(bool enablePlugins)
{
    assert(plugins.empty());

    if (!enablePlugins) {
        // [#2159] list but don't enable the plugins
        return;
    }

    const QString userPluginDir = getUserPluginsDirectory();
    if (!userPluginDir.isEmpty()) {
        loadPluginsFromDir(QDir(userPluginDir), true);
    }
    const auto pluginDirs = getPluginDirectories();
    for (auto &dir : pluginDirs) {
        if (dir.absolutePath() == userPluginDir) {
            continue;
        }
        loadPluginsFromDir(dir);
    }
}

void PluginManager::loadPluginsFromDir(const QDir &pluginsDir, bool writable)
{
    qInfo() << "Plugins are loaded from" << pluginsDir.absolutePath();
    int loadedPlugins = plugins.size();
    if (!pluginsDir.exists()) {
        return;
    }

    QDir nativePluginsDir = pluginsDir;
    if (writable) {
        nativePluginsDir.mkdir("native");
    }
    if (nativePluginsDir.cd("native")) {
        qInfo() << "Native plugins are loaded from" << nativePluginsDir.absolutePath();
        loadNativePlugins(nativePluginsDir);
    }

#ifdef CLUTTER_ENABLE_PYTHON_BINDINGS
    QDir pythonPluginsDir = pluginsDir;
    if (writable) {
        pythonPluginsDir.mkdir("python");
    }
    if (pythonPluginsDir.cd("python")) {
        qInfo() << "Python plugins are loaded from" << pythonPluginsDir.absolutePath();
        loadPythonPlugins(pythonPluginsDir.absolutePath());
    }
#endif

    loadedPlugins = plugins.size() - loadedPlugins;
    qInfo() << "Loaded" << loadedPlugins << "plugin(s).";
}

void PluginManager::PluginTerminator::operator()(ClutterPlugin *plugin) const
{
    plugin->terminate();
    delete plugin;
}

void PluginManager::destroyPlugins()
{
    plugins.clear();
}

QVector<QDir> PluginManager::getPluginDirectories() const
{
    QVector<QDir> result;
    const QStringList locations = Clutter::standardLocations(QStandardPaths::AppDataLocation);
    for (auto &location : locations) {
        result.push_back(QDir(location).filePath("plugins"));
    }

#if QT_VERSION < QT_VERSION_CHECK(5, 6, 0) && defined(Q_OS_UNIX)
    QChar listSeparator = ':';
#else
    const QChar listSeparator = QDir::listSeparator();
#endif
    const QString extraPluginDirs = CLUTTER_EXTRA_PLUGIN_DIRS;
    for (auto &path : extraPluginDirs.split(listSeparator, CLUTTER_QT_SKIP_EMPTY_PARTS)) {
        result.push_back(QDir(path));
    }

    return result;
}

QString PluginManager::getUserPluginsDirectory() const
{
    const QString location = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation);
    if (location.isEmpty()) {
        return QString();
    }
    QDir pluginsDir(location);
    pluginsDir.mkpath("plugins");
    if (!pluginsDir.cd("plugins")) {
        return QString();
    }
    return pluginsDir.absolutePath();
}

void PluginManager::loadNativePlugins(const QDir &directory)
{
    for (const QString &fileName : directory.entryList(QDir::Files)) {
        if (!QLibrary::isLibrary(fileName)) {
            // Reduce amount of warnings, by not attempting files which are obviously not plugins
            continue;
        }
        QPluginLoader pluginLoader(directory.absoluteFilePath(fileName));
        QObject *plugin = pluginLoader.instance();
        if (!plugin) {
            auto errorString = pluginLoader.errorString();
            if (!errorString.isEmpty()) {
                qWarning() << "Load Error for plugin" << fileName << ":" << errorString;
            }
            continue;
        }
        PluginPtr clutterPlugin { qobject_cast<ClutterPlugin *>(plugin) };
        if (!clutterPlugin) {
            continue;
        }
        clutterPlugin->setupPlugin();
        plugins.push_back(std::move(clutterPlugin));
    }
}

#ifdef CLUTTER_ENABLE_PYTHON_BINDINGS

void PluginManager::loadPythonPlugins(const QDir &directory)
{
    Python()->addPythonPath(directory.absolutePath().toLocal8Bit().data());

    for (const QString &fileName :
         directory.entryList(QDir::Dirs | QDir::Files | QDir::NoDotAndDotDot)) {
        if (fileName == "__pycache__") {
            continue;
        }
        QString moduleName;
        if (fileName.endsWith(".py")) {
            moduleName = fileName.chopped(3);
        } else {
            moduleName = fileName;
        }
        PluginPtr clutterPlugin { loadPythonPlugin(moduleName.toLocal8Bit().constData()) };
        if (!clutterPlugin) {
            continue;
        }
        clutterPlugin->setupPlugin();
        plugins.push_back(std::move(clutterPlugin));
    }

    PythonManager::ThreadHolder threadHolder;
}

ClutterPlugin *PluginManager::loadPythonPlugin(const char *moduleName)
{
    PythonManager::ThreadHolder threadHolder;

    PyObject *pluginModule = PyImport_ImportModule(moduleName);
    if (!pluginModule) {
        qWarning() << "Couldn't load module for plugin:" << QString(moduleName);
        PyErr_Print();
        return nullptr;
    }

    // "create_cutter_plugin" is accepted as well, so Python plugins written
    // against upstream Cutter keep loading (see README, "Rebrand and
    // compatibility").
    PyObject *createPluginFunc = PyObject_GetAttrString(pluginModule, "create_clutter_plugin");
    if (!createPluginFunc || !PyCallable_Check(createPluginFunc)) {
        PyErr_Clear();
        if (createPluginFunc) {
            Py_DECREF(createPluginFunc);
        }
        createPluginFunc = PyObject_GetAttrString(pluginModule, "create_cutter_plugin");
    }
    if (!createPluginFunc || !PyCallable_Check(createPluginFunc)) {
        PyErr_Clear();
        qWarning() << "Plugin module does not contain create_clutter_plugin() function:"
                   << QString(moduleName);
        if (createPluginFunc) {
            Py_DECREF(createPluginFunc);
        }
        Py_DECREF(pluginModule);
        return nullptr;
    }

    PyObject *pluginObject = PyObject_CallFunction(createPluginFunc, nullptr);
    Py_DECREF(createPluginFunc);
    Py_DECREF(pluginModule);
    if (!pluginObject) {
        qWarning() << "Plugin's create_clutter_plugin() function failed.";
        PyErr_Print();
        return nullptr;
    }

    PythonToCppFunc pythonToCpp = Shiboken::Conversions::isPythonToCppPointerConvertible(
#    if QT_VERSION < QT_VERSION_CHECK(6, 0, 0)
            reinterpret_cast<SbkObjectType *>(SbkClutterBindingsTypes[SBK_CLUTTERPLUGIN_IDX]),
#    elif QT_VERSION < QT_VERSION_CHECK(6, 2, 0)
            reinterpret_cast<SbkObjectType *>(SbkClutterBindingsTypes[SBK_ClutterPlugin_IDX]),
#    else
            reinterpret_cast<PyTypeObject **>(SbkClutterBindingsTypeStructs)[SBK_ClutterPlugin_IDX],
#    endif
            pluginObject);
    if (!pythonToCpp) {
        qWarning() << "Plugin's create_clutter_plugin() function did not return an instance of "
                      "ClutterPlugin:"
                   << QString(moduleName);
        return nullptr;
    }
    ClutterPlugin *plugin;
    pythonToCpp(pluginObject, &plugin);
    if (!plugin) {
        qWarning() << "Error during the setup of ClutterPlugin:" << QString(moduleName);
        return nullptr;
    }
    return plugin;
}
#endif
