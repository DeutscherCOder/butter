#ifndef BUTTERTREEVIEW_H
#define BUTTERTREEVIEW_H

#include "core/ButterCommon.h"

#include <QAbstractItemView>
#include <QTreeView>

#include <memory>

namespace Ui {
class ButterTreeView;
}

/**
 * @brief QTreeView wrapper for Butter for default style and functionality
 */
class BUTTER_EXPORT ButterTreeView : public QTreeView
{
    Q_OBJECT

public:
    explicit ButterTreeView(QWidget *parent = nullptr);
    ~ButterTreeView();

    static void applyButterStyle(QTreeView *view);

private:
    std::unique_ptr<Ui::ButterTreeView> ui;
};

#endif // BUTTERTREEVIEW_H
