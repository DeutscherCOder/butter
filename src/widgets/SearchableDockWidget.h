#ifndef SEARCHABLEDOCKWIDGET_H
#define SEARCHABLEDOCKWIDGET_H

#include "ButterDockWidget.h"
#include "ButterSearchable.h"

class SearchBarWidget;

/**
 * @brief A dock widget that includes a search bar
 */
class BUTTER_EXPORT SearchableDockWidget : public ButterDockWidget, public ButterSearchableI
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
