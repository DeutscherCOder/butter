#include "ButterDockWidget.h"

#include "core/MainWindow.h"
#include "shortcuts/ShortcutManager.h"

#include <QApplication>
#include <QEvent>
#include <QShortcut>

ButterDockWidget::ButterDockWidget(MainWindow *parent, QAction *) : ButterDockWidget(parent) {}

ButterDockWidget::ButterDockWidget(MainWindow *parent) : QDockWidget(parent), mainWindow(parent)
{
    // Install event filter to catch redraw widgets when needed
    installEventFilter(this);
    updateIsVisibleToUser();
    connect(toggleViewAction(), &QAction::triggered, this, &QWidget::raise);
}

bool ButterDockWidget::event(QEvent *event)
{

    if (event->type() == QEvent::Move || event->type() == QEvent::MouseMove) {

        const Qt::KeyboardModifiers mods = QApplication::keyboardModifiers();
        const Qt::KeyboardModifier mod =
                Shortcuts()->convertKeyToModifer(Shortcuts()->getKeySequence("Docking.toggle"));

        if (mods & mod) {
            setAllowedAreas(Qt::NoDockWidgetArea);
        } else {
            setAllowedAreas(Qt::AllDockWidgetAreas);
        }
    }
    return QDockWidget::event(event);
}

ButterDockWidget::~ButterDockWidget() = default;

bool ButterDockWidget::eventFilter(QObject *object, QEvent *event)
{
    if (event->type() == QEvent::FocusIn || event->type() == QEvent::ZOrderChange
        || event->type() == QEvent::Paint || event->type() == QEvent::Close
        || event->type() == QEvent::Show || event->type() == QEvent::Hide) {
        updateIsVisibleToUser();
    }
    return QDockWidget::eventFilter(object, event);
}

QVariantMap ButterDockWidget::serializeViewProprties()
{
    return {};
}

void ButterDockWidget::deserializeViewProperties(const QVariantMap &) {}

void ButterDockWidget::ignoreVisibilityStatus(bool ignore)
{
    this->ignoreVisibility = ignore;
    updateIsVisibleToUser();
}

void ButterDockWidget::raiseMemoryWidget()
{
    show();
    raise();
    widgetToFocusOnRaise()->setFocus(Qt::FocusReason::TabFocusReason);
}

void ButterDockWidget::toggleDockWidget(bool show)
{
    if (!show) {
        this->hide();
    } else {
        this->show();
        this->raise();
    }
}

QWidget *ButterDockWidget::widgetToFocusOnRaise()
{
    return this;
}

void ButterDockWidget::updateIsVisibleToUser()
{
    // Check if the user can actually see the widget.
    const bool visibleToUser = isVisible() && !visibleRegion().isEmpty() && !ignoreVisibility;
    if (visibleToUser == isVisibleToUserCurrent) {
        return;
    }
    isVisibleToUserCurrent = visibleToUser;
    if (isVisibleToUserCurrent) {
        emit becameVisibleToUser();
    }
}

void ButterDockWidget::closeEvent(QCloseEvent *event)
{
    QDockWidget::closeEvent(event);
    if (isTransient) {
        if (mainWindow) {
            mainWindow->removeWidget(this);
        }

        // remove parent, otherwise dock layout may still decide to use this widget which is about
        // to be deleted
        setParent(nullptr);

        deleteLater();
    }

    emit closed();
}

QString ButterDockWidget::getDockNumber()
{
    auto name = this->objectName();
    if (name.contains(';')) {
        auto parts = name.split(';');
        if (parts.size() >= 2) {
            return parts[1];
        }
    }
    return QString();
}
