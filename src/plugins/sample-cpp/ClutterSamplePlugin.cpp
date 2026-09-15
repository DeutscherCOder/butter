#include "ClutterSamplePlugin.h"

#include <QAction>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>

#include <MainWindow.h>
#include <common/Configuration.h>
#include <common/TempConfig.h>
#include <rz_core.h>

void ClutterSamplePlugin::setupPlugin() {}

void ClutterSamplePlugin::setupInterface(MainWindow *main)
{
    ClutterSamplePluginWidget *widget = new ClutterSamplePluginWidget(main);
    main->addPluginDockWidget(widget);
}

ClutterSamplePluginWidget::ClutterSamplePluginWidget(MainWindow *main) : ClutterDockWidget(main)
{
    this->setObjectName("ClutterSamplePluginWidget");
    this->setWindowTitle("Sample C++ Plugin");
    QWidget *content = new QWidget();
    this->setWidget(content);

    QVBoxLayout *layout = new QVBoxLayout(content);
    content->setLayout(layout);
    text = new QLabel(content);
    text->setFont(Config()->getFont());
    text->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Preferred);
    layout->addWidget(text);

    QPushButton *button = new QPushButton(content);
    button->setText("Want a fortune?");
    button->setSizePolicy(QSizePolicy::Maximum, QSizePolicy::Maximum);
    button->setMaximumHeight(50);
    button->setMaximumWidth(200);
    layout->addWidget(button);
    layout->setAlignment(button, Qt::AlignHCenter);

    connect(Core(), &ClutterCore::seekChanged, this, &ClutterSamplePluginWidget::on_seekChanged);
    connect(button, &QPushButton::clicked, this, &ClutterSamplePluginWidget::on_buttonClicked);
}

void ClutterSamplePluginWidget::on_seekChanged(RVA addr)
{
    Q_UNUSED(addr);
    RzCoreLocked core(Core());
    TempConfig tempConfig;
    tempConfig.set("scr.color", 0);
    QString disasm = Core()->disassembleSingleInstruction(Core()->getOffset());
    QString res = fromOwnedCharPtr(rz_core_clippy(core, disasm.toUtf8().constData()));
    text->setText(res);
}

void ClutterSamplePluginWidget::on_buttonClicked()
{
    RzCoreLocked core(Core());
    auto fortune = fromOwned(rz_core_fortune_get_random(core));
    if (!fortune) {
        return;
    }
    QString res = fromOwnedCharPtr(rz_core_clippy(core, fortune.get()));
    text->setText(res);
}
