#include "AddressableDockWidget.h"

#include "MainWindow.h"
#include "common/ClutterSeekable.h"

#include <QAction>
#include <QContextMenuEvent>
#include <QEvent>
#include <QMenu>

AddressableDockWidget::AddressableDockWidget(MainWindow *parent)
    : ClutterDockWidget(parent),
      seekable(new ClutterSeekable(this)),
      syncAction(tr("Sync/unsync offset"), this),
      dockMenu(new QMenu(this))
{
    connect(seekable, &ClutterSeekable::syncChanged, this,
            &AddressableDockWidget::updateWindowTitle);
    connect(&syncAction, &QAction::triggered, seekable, &ClutterSeekable::toggleSynchronization);

    dockMenu->addAction(&syncAction);

    setContextMenuPolicy(Qt::ContextMenuPolicy::DefaultContextMenu);
}

QVariantMap AddressableDockWidget::serializeViewProprties()
{
    auto result = ClutterDockWidget::serializeViewProprties();
    result["synchronized"] = seekable->isSynchronized();
    return result;
}

void AddressableDockWidget::deserializeViewProperties(const QVariantMap &properties)
{
    const QVariant synchronized = properties.value("synchronized", true);
    seekable->setSynchronization(synchronized.toBool());
}

void AddressableDockWidget::updateWindowTitle()
{
    QString name = getWindowTitle();
    const QString id = getDockNumber();
    if (!id.isEmpty()) {
        name += " " + id;
    }
    if (!seekable->isSynchronized()) {
        name += ClutterSeekable::tr(" (unsynced)");
    }
    setWindowTitle(name);
}

void AddressableDockWidget::contextMenuEvent(QContextMenuEvent *event)
{
    event->accept();
    dockMenu->exec(mapToGlobal(event->pos()));
}

ClutterSeekable *AddressableDockWidget::getSeekable() const
{
    return seekable;
}
