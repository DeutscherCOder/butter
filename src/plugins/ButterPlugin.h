#ifndef BUTTERPLUGIN_H
#define BUTTERPLUGIN_H

class MainWindow;

#include "widgets/ButterDockWidget.h"

/**
 * @brief Interface for defining any Butter plugin
 */
class BUTTER_EXPORT ButterPlugin
{
public:
    virtual ~ButterPlugin() = default;

    /**
     * @brief Initialize the Plugin
     *
     * called right when the plugin is loaded initially
     */
    virtual void setupPlugin() = 0;

    /**
     * @brief Setup any UI components for the Plugin
     * @param main the MainWindow to add any UI to
     *
     * called after Butter's core UI has been initialized
     */
    virtual void setupInterface(MainWindow *main) = 0;

    /**
     * @brief Register any decompiler implemented by the Plugin
     *
     * called during initialization of Butter, after setupPlugin()
     */
    virtual void registerDecompilers() {}

    /**
     * @brief Shutdown the Plugin
     *
     * called just before the Plugin is deleted.
     * This method is usually only relevant for Python Plugins where there is no
     * direct equivalent of the destructor.
     */
    virtual void terminate() {};

    virtual QString getName() const = 0;
    virtual QString getAuthor() const = 0;
    virtual QString getDescription() const = 0;
    virtual QString getVersion() const = 0;
};

#define ButterPlugin_iid "re.rizin.butter.plugins.ButterPlugin"

Q_DECLARE_INTERFACE(ButterPlugin, ButterPlugin_iid)

#endif // BUTTERPLUGIN_H
