#ifndef CLUTTERTREEVIEW_H
#define CLUTTERTREEVIEW_H

#include "core/ClutterCommon.h"

#include <QAbstractItemView>
#include <QTreeView>

#include <memory>

namespace Ui {
class ClutterTreeView;
}

/**
 * @brief QTreeView wrapper for Clutter for default style and functionality
 */
class CLUTTER_EXPORT ClutterTreeView : public QTreeView
{
    Q_OBJECT

public:
    explicit ClutterTreeView(QWidget *parent = nullptr);
    ~ClutterTreeView();

    static void applyClutterStyle(QTreeView *view);

private:
    std::unique_ptr<Ui::ClutterTreeView> ui;
};

#endif // CLUTTERTREEVIEW_H
