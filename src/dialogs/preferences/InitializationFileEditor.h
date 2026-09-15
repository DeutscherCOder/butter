#ifndef INITIALIZATIONFILEEDITOR_H
#define INITIALIZATIONFILEEDITOR_H

#include <QDialog>
#include <QPushButton>

#include <memory>

class PreferencesDialog;

namespace Ui {
class InitializationFileEditor;
}

/**
 * @brief An editor for Clutter initialization script
 */
class InitializationFileEditor : public QDialog
{
    Q_OBJECT

public:
    explicit InitializationFileEditor(PreferencesDialog *dialog);
    ~InitializationFileEditor();
    void saveClutterRC();
    void executeClutterRC();

private:
    std::unique_ptr<Ui::InitializationFileEditor> ui;
};

#endif // INITIALIZATIONFILEEDITOR_H
