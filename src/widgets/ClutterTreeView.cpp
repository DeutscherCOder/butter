#include "ClutterTreeView.h"

#include "ui_ClutterTreeView.h"

ClutterTreeView::ClutterTreeView(QWidget *parent) : QTreeView(parent), ui(new Ui::ClutterTreeView())
{
    ui->setupUi(this);
    applyClutterStyle(this);
}

ClutterTreeView::~ClutterTreeView() {}

void ClutterTreeView::applyClutterStyle(QTreeView *view)
{
    view->setSelectionMode(QAbstractItemView::ExtendedSelection);
    view->setUniformRowHeights(true);
}
