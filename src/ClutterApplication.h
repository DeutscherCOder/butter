#ifndef CLUTTERAPPLICATION_H
#define CLUTTERAPPLICATION_H

#include "core/MainWindow.h"

#include <QApplication>
#include <QEvent>
#include <QList>
#include <QProxyStyle>

enum class AutomaticAnalysisLevel : ut8 { Ask, None, AAA, AAAA };

struct ClutterCommandLineOptions
{
    QStringList args;
    AutomaticAnalysisLevel analysisLevel = AutomaticAnalysisLevel::Ask;
    InitialOptions fileOpenOptions;
    QString pythonHome;
    bool outputRedirectionEnabled = true;
    bool enableClutterPlugins = true;
    bool enableRizinPlugins = true;
};

/**
 * @brief Main application class for Clutter
 */
class ClutterApplication : public QApplication
{
    Q_OBJECT

public:
    ClutterApplication(int &argc, char **argv);
    ~ClutterApplication();

    MainWindow *getMainWindow() { return mainWindow; }

    void launchNewInstance(const QStringList &args = {});

    InitialOptions getInitialOptions() const { return clOptions.fileOpenOptions; }
    void setInitialOptions(const InitialOptions &options) { clOptions.fileOpenOptions = options; }
    QStringList getArgs() const;

protected:
    bool event(QEvent *e);

private:
    /**
     * @brief Load and translations depending on Language settings
     * @return true on success
     */
    bool loadTranslations();
    /**
     * @brief Parse commandline options and store them in a structure.
     * @return false if options have error
     */
    bool parseCommandLineOptions();

private:
    bool fileAlreadyDropped;
    ClutterCore core;
    MainWindow *mainWindow;
    ClutterCommandLineOptions clOptions;
};

/**
 * @brief ClutterProxyStyle is used to force shortcuts displaying in context menu
 */
class ClutterProxyStyle : public QProxyStyle
{
    Q_OBJECT
public:
    /**
     * @brief it is enough to get notification about QMenu polishing to force shortcut displaying
     */
    void polish(QWidget *widget) override;
};

#endif // CLUTTERAPPLICATION_H
