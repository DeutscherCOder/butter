#ifndef ADDRESSABLE_DOCK_WIDGET_H
#define ADDRESSABLE_DOCK_WIDGET_H

#include "ButterDockWidget.h"

#include <QAction>

class ButterSeekable;

/**
 * @brief Base class for dock widgets that support synchronization with a specific address/offset
 */
class AddressableDockWidget : public ButterDockWidget
{
    Q_OBJECT
public:
    AddressableDockWidget(MainWindow *parent);
    ~AddressableDockWidget() override {}

    ButterSeekable *getSeekable() const;

    QVariantMap serializeViewProprties() override;
    void deserializeViewProperties(const QVariantMap &properties) override;
public slots:
    void updateWindowTitle();

protected:
    ButterSeekable *seekable = nullptr;
    QAction syncAction;
    QMenu *dockMenu = nullptr;

    virtual QString getWindowTitle() const = 0;
    void contextMenuEvent(QContextMenuEvent *event) override;
};

#endif // ADDRESSABLE_DOCK_WIDGET_H
