#ifndef SEARCHABLEDOCKWIDGET_H
#define SEARCHABLEDOCKWIDGET_H

#include "ClutterDockWidget.h"
#include "ClutterSearchable.h"

class SearchBarWidget;

/**
 * @brief A dock widget that includes a search bar
 */
class CLUTTER_EXPORT SearchableDockWidget : public ClutterDockWidget, public ClutterSearchableI
{
    Q_OBJECT

public:
    explicit SearchableDockWidget(MainWindow *parent);

    void updateSearchBarPosition();

protected:
    SearchBarWidget *searchBar;

    void resizeEvent(QResizeEvent *event) override;
    int searchHPadding() const override;
    int searchVPadding() const override;

private:
};

#endif // SEARCHABLEDOCKWIDGET_H
