#include "SearchableDockWidget.h"

#include "SearchBarWidget.h"

#include <QAbstractScrollArea>
#include <QScrollBar>
#include <QTimer>

namespace {
constexpr int hPadding = 7;
constexpr int vPadding = 4;
};

SearchableDockWidget::SearchableDockWidget(MainWindow *parent)
    : ClutterDockWidget(parent), searchBar(new SearchBarWidget(this))
{
    ClutterSearchableHelper::setupConnections(this, searchBar);
}

void SearchableDockWidget::resizeEvent(QResizeEvent *event)
{
    ClutterDockWidget::resizeEvent(event);
    updateSearchBarPosition();
}

void SearchableDockWidget::updateSearchBarPosition()
{
    ClutterSearchableHelper::positionSearchBar(this, searchBar, searchableArea(), searchHPadding(),
                                              searchVPadding());
}

int SearchableDockWidget::searchHPadding() const
{
    return hPadding;
}

int SearchableDockWidget::searchVPadding() const
{
    return vPadding;
}
