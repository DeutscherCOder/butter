#ifndef WELCOMEDIALOG_H
#define WELCOMEDIALOG_H

#include <QDialog>

#include <memory>

namespace Ui {

class WelcomeDialog;
}

/**
 * @brief The WelcomeDialog class will show the user the Welcome windows
 * upon first execution of Clutter.
 *
 * The Welcome dialog would also be showed after a reset of Clutter's preferences by the user.
 */
class WelcomeDialog : public QDialog
{
    Q_OBJECT

public:
    explicit WelcomeDialog(QWidget *parent = nullptr);
    ~WelcomeDialog();

private slots:
    /**
     * @brief change Clutter's QT Theme as selected by the user
     * @param index - a Slot being called after theme's value changes its index
     */
    void onThemeComboBoxCurrentIndexChanged(int index);
    /**
     * @brief change Clutter's interface language as selected by the user
     * @param index - a Slot being called after language combo box value changes its index
     */
    void onLanguageCurrentIndexChanged(int index);
    /**
     * @brief show Clutter's About dialog
     */
    void onCheckUpdateButtonClicked();
    /**
     * @brief accept user preferences, close the window and continue Clutter's execution
     */
    void onContinueButtonClicked();
    void onUpdatesCheckBoxStateChanged(int state);

private:
    std::unique_ptr<Ui::WelcomeDialog> ui;
};

#endif // WELCOMEDIALOG_H
