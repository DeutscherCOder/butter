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
    connect(ui->saveRC, &QDialogButtonBox::accepted, this, &InitializationFileEditor::saveClutterRC);
    connect(ui->executeNow, &QDialogButtonBox::accepted, this,
            &InitializationFileEditor::executeClutterRC);
    connect(ui->configFileEdit, &QPlainTextEdit::modificationChanged, ui->saveRC,
            &QWidget::setEnabled);

    const QDir clutterRCDirectory = Core()->getClutterRCDefaultDirectory();
    auto clutterRCFileInfo = QFileInfo(clutterRCDirectory, "rc");
    const QString clutterRCLocation = clutterRCFileInfo.absoluteFilePath();

    ui->clutterRCLoaded->setTextInteractionFlags(Qt::TextBrowserInteraction);
    ui->clutterRCLoaded->setOpenExternalLinks(true);
    ui->clutterRCLoaded->setText(
            tr("Script is loaded from <a href=\"%1\">%2</a>")
                    .arg(QUrl::fromLocalFile(clutterRCDirectory.absolutePath()).toString(),
                         clutterRCLocation.toHtmlEscaped()));

    ui->executeNow->button(QDialogButtonBox::Retry)->setText(tr("Execute", "script"));
    ui->configFileEdit->clear();
    if (clutterRCFileInfo.exists()) {
        QFile clutterRC(clutterRCLocation);
        if (clutterRC.open(QIODevice::ReadWrite | QIODevice::Text)) {
            ui->configFileEdit->setPlainText(clutterRC.readAll());
        }
        clutterRC.close();
    }
    ui->saveRC->setDisabled(true);
}

InitializationFileEditor::~InitializationFileEditor() {};

void InitializationFileEditor::saveClutterRC()
{
    const QDir clutterRCDirectory = Core()->getClutterRCDefaultDirectory();
    if (!clutterRCDirectory.exists()) {
        clutterRCDirectory.mkpath(".");
    }
    auto clutterRCFileInfo = QFileInfo(clutterRCDirectory, "rc");
    const QString clutterRCLocation = clutterRCFileInfo.absoluteFilePath();

    QFile clutterRC(clutterRCLocation);
    if (clutterRC.open(QIODevice::ReadWrite | QIODevice::Truncate | QIODevice::Text)) {
        QTextStream out(&clutterRC);
        const QString text = ui->configFileEdit->toPlainText();
        out << text;
        clutterRC.close();
    }
    ui->configFileEdit->document()->setModified(false);
}

void InitializationFileEditor::executeClutterRC()
{
    saveClutterRC();
    Core()->loadDefaultClutterRC();
}
