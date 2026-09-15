#ifndef ADDRESSABLE_DOCK_WIDGET_H
#define ADDRESSABLE_DOCK_WIDGET_H

#include "ClutterDockWidget.h"

#include <QAction>

class ClutterSeekable;

/**
 * @brief Base class for dock widgets that support synchronization with a specific address/offset
 */
class AddressableDockWidget : public ClutterDockWidget
{
    Q_OBJECT
public:
    AddressableDockWidget(MainWindow *parent);
    ~AddressableDockWidget() override {}

    ClutterSeekable *getSeekable() const;

    QVariantMap serializeViewProprties() override;
    void deserializeViewProperties(const QVariantMap &properties) override;
public slots:
    void updateWindowTitle();

protected:
    ClutterSeekable *seekable = nullptr;
    QAction syncAction;
    QMenu *dockMenu = nullptr;

    virtual QString getWindowTitle() const = 0;
    void contextMenuEvent(QContextMenuEvent *event) override;
};

#endif // ADDRESSABLE_DOCK_WIDGET_H
