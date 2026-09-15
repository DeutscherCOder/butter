#include "RefreshDeferrer.h"

#include "widgets/ClutterDockWidget.h"

RefreshDeferrer::RefreshDeferrer(RefreshDeferrerAccumulator *acc, QObject *parent)
    : QObject(parent), acc(acc)
{
}

RefreshDeferrer::~RefreshDeferrer()
{
    delete acc;
}

bool RefreshDeferrer::attemptRefresh(RefreshDeferrerParams params)
{
    if (dockWidget->isVisibleToUser()) {
        if (acc) {
            acc->ignoreParams(params);
        }
        return true;
    } else {
        dirty = true;
        if (acc) {
            acc->accumulate(params);
        }
        return false;
    }
}

void RefreshDeferrer::registerFor(ClutterDockWidget *dockWidget)
{
    this->dockWidget = dockWidget;
    connect(dockWidget, &ClutterDockWidget::becameVisibleToUser, this, [this]() {
        if (dirty) {
            emit refreshNow(acc ? acc->result() : nullptr);
            if (acc) {
                acc->clear();
            }
            dirty = false;
        }
    });
}
