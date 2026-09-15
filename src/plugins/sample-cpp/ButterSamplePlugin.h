#ifndef BUTTERSAMPLEPLUGIN_H
#define BUTTERSAMPLEPLUGIN_H

#include <QLabel>

#include <ButterPlugin.h>

class ButterSamplePlugin : public QObject, ButterPlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA(IID "re.rizin.butter.plugins.ButterPlugin")
    Q_INTERFACES(ButterPlugin)

public:
    void setupPlugin() override;
    void setupInterface(MainWindow *main) override;

    QString getName() const override { return "SamplePlugin"; }
    QString getAuthor() const override { return "xarkes"; }
    QString getDescription() const override { return "Just a sample plugin."; }
    QString getVersion() const override { return "1.0"; }
};

class ButterSamplePluginWidget : public ButterDockWidget
{
    Q_OBJECT

public:
    explicit ButterSamplePluginWidget(MainWindow *main);

private:
    QLabel *text;

private slots:
    void on_seekChanged(RVA addr);
    void on_buttonClicked();
};

#endif // BUTTERSAMPLEPLUGIN_H
