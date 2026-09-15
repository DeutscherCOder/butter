#include "InitializationFileEditor.h"

#include "PreferencesDialog.h"
#include "common/Helpers.h"
#include "ui_InitializationFileEditor.h"

#include <QDialogButtonBox>
#include <QDir>
#include <QFile>
#include <QFontDialog>
#include <QLabel>
#include <QTextEdit>
#include <QTextStream>
#include <QUrl>

InitializationFileEditor::InitializationFileEditor(PreferencesDialog *dialog)
    : QDialog(dialog), ui(new Ui::InitializationFileEditor)
{
    ui->setupUi(this);
    connect(ui->saveRC, &QDialogButtonBox::accepted, this, &InitializationFileEditor::saveButterRC);
    connect(ui->executeNow, &QDialogButtonBox::accepted, this,
            &InitializationFileEditor::executeButterRC);
    connect(ui->configFileEdit, &QPlainTextEdit::modificationChanged, ui->saveRC,
            &QWidget::setEnabled);

    const QDir butterRCDirectory = Core()->getButterRCDefaultDirectory();
    auto butterRCFileInfo = QFileInfo(butterRCDirectory, "rc");
    const QString butterRCLocation = butterRCFileInfo.absoluteFilePath();

    ui->butterRCLoaded->setTextInteractionFlags(Qt::TextBrowserInteraction);
    ui->butterRCLoaded->setOpenExternalLinks(true);
    ui->butterRCLoaded->setText(
            tr("Script is loaded from <a href=\"%1\">%2</a>")
                    .arg(QUrl::fromLocalFile(butterRCDirectory.absolutePath()).toString(),
                         butterRCLocation.toHtmlEscaped()));

    ui->executeNow->button(QDialogButtonBox::Retry)->setText(tr("Execute", "script"));
    ui->configFileEdit->clear();
    if (butterRCFileInfo.exists()) {
        QFile butterRC(butterRCLocation);
        if (butterRC.open(QIODevice::ReadWrite | QIODevice::Text)) {
            ui->configFileEdit->setPlainText(butterRC.readAll());
        }
        butterRC.close();
    }
    ui->saveRC->setDisabled(true);
}

InitializationFileEditor::~InitializationFileEditor() {};

void InitializationFileEditor::saveButterRC()
{
    const QDir butterRCDirectory = Core()->getButterRCDefaultDirectory();
    if (!butterRCDirectory.exists()) {
        butterRCDirectory.mkpath(".");
    }
    auto butterRCFileInfo = QFileInfo(butterRCDirectory, "rc");
    const QString butterRCLocation = butterRCFileInfo.absoluteFilePath();

    QFile butterRC(butterRCLocation);
    if (butterRC.open(QIODevice::ReadWrite | QIODevice::Truncate | QIODevice::Text)) {
        QTextStream out(&butterRC);
        const QString text = ui->configFileEdit->toPlainText();
        out << text;
        butterRC.close();
    }
    ui->configFileEdit->document()->setModified(false);
}

void InitializationFileEditor::executeButterRC()
{
    saveButterRC();
    Core()->loadDefaultButterRC();
}
