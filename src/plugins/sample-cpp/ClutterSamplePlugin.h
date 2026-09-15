#ifndef CLUTTERSAMPLEPLUGIN_H
#define CLUTTERSAMPLEPLUGIN_H

#include <QLabel>

#include <ClutterPlugin.h>

class ClutterSamplePlugin : public QObject, ClutterPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "re.rizin.clutter.plugins.ClutterPlugin")
    Q_INTERFACES(ClutterPlugin)

public:
    void setupPlugin() override;
    void setupInterface(MainWindow *main) override;

    QString getName() const override { return "SamplePlugin"; }
    QString getAuthor() const override { return "xarkes"; }
    QString getDescription() const override { return "Just a sample plugin."; }
    QString getVersion() const override { return "1.0"; }
};

class ClutterSamplePluginWidget : public ClutterDockWidget
{
    Q_OBJECT

public:
    explicit ClutterSamplePluginWidget(MainWindow *main);

private:
    QLabel *text;

private slots:
    void on_seekChanged(RVA addr);
    void on_buttonClicked();
};

#endif // CLUTTERSAMPLEPLUGIN_H
