#ifndef HEAPDOCKWIDGET_H
#define HEAPDOCKWIDGET_H

#include "ButterDockWidget.h"

#include <QDockWidget>

#include <memory>

namespace Ui {
class HeapDockWidget;
}

/**
 * @brief A container widget that serves as the primary interface for heap analysis
 */
class HeapDockWidget : public ButterDockWidget
{
    Q_OBJECT

public:
    explicit HeapDockWidget(MainWindow *main);
    ~HeapDockWidget();
private slots:
    void onAllocatorSelected(int index);

private:
    enum Allocator : ut8 { Glibc = 0, AllocatorCount };
    std::unique_ptr<Ui::HeapDockWidget> ui;
    MainWindow *main;
    QWidget *currentHeapWidget = nullptr;
};

#endif // HEAPDOCKWIDGET_H
