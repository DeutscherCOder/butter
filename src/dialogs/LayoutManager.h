#ifndef LAYOUT_MANAGER_H
#define LAYOUT_MANAGER_H

#include "common/ClutterLayout.h"

#include <QDialog>

#include <memory>

namespace Ui {
class LayoutManager;
}

/**
 * @brief Dialog for managing custom UI layouts
 */
class LayoutManager : public QDialog
{
    Q_OBJECT

public:
    LayoutManager(QMap<QString, Clutter::ClutterLayout> &layouts, QWidget *parent);
    ~LayoutManager();

private:
    void refreshNameList(const QString &selection = "");
    void renameCurrentLayout();
    void deleteLayout();
    void updateButtons();
    std::unique_ptr<Ui::LayoutManager> ui;
    QMap<QString, Clutter::ClutterLayout> &layouts;
};

#endif // LAYOUT_MANAGER_H
