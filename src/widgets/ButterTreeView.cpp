#include "ButterTreeView.h"

#include "ui_ButterTreeView.h"

ButterTreeView::ButterTreeView(QWidget *parent) : QTreeView(parent), ui(new Ui::ButterTreeView())
{
    ui->setupUi(this);
    applyButterStyle(this);
}

ButterTreeView::~ButterTreeView() {}

void ButterTreeView::applyButterStyle(QTreeView *view)
{
    view->setSelectionMode(QAbstractItemView::ExtendedSelection);
    view->setUniformRowHeights(true);
}
