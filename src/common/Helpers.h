#ifndef QHELPERS_H
#define QHELPERS_H

#include "core/ButterCommon.h"

#include <QColor>
#include <QSizePolicy>
#include <QString>

#include <functional>

class QIcon;
class QPlainTextEdit;
class QTextEdit;
class QString;
class QTreeWidget;
class QTreeWidgetItem;
class QAbstractItemView;
class QAbstractItemModel;
class QAbstractButton;
class QWidget;
class QTreeView;
class QAction;
class QMenu;
class QPaintDevice;
class QComboBox;
class QSortFilterProxyModel;
class QMouseEvent;

#if QT_VERSION < QT_VERSION_CHECK(5, 14, 0)
#    define BUTTER_QT_SKIP_EMPTY_PARTS QString::SkipEmptyParts
#else
#    define BUTTER_QT_SKIP_EMPTY_PARTS Qt::SkipEmptyParts
#endif

/**
 * @namespace Helpers for QT related objects
 */
namespace qhelpers {
BUTTER_EXPORT QString formatByteCount(ut64 bytecount);
BUTTER_EXPORT void adjustColumns(QTreeView *tv, int columnCount, int padding);
BUTTER_EXPORT void adjustColumns(QTreeView *tw, int startIndex, int endIndex, int padding);
BUTTER_EXPORT void adjustColumns(QTreeWidget *tw, int padding);
/**
 * @brief Resize column to contents or speicifed width
 *
 * Width is only applied if it's non-negative and less than the width of
 * specified columns contents
 *
 * @param tv TreeView which contains the column
 * @param columnIndex The index of column to resize
 * @param width Width in pixels for resizing the column
 */
BUTTER_EXPORT void adjustColumn(QTreeView *tv, int columnIndex, int width = -1);

/**
 * @brief Select first item of a QAbstractItemView if not empty
 * @param itemView
 * @return true if first item was selected
 */
BUTTER_EXPORT bool selectFirstItem(QAbstractItemView *itemView);
BUTTER_EXPORT QTreeWidgetItem *appendRow(QTreeWidget *tw, const QString &str,
                                         const QString &str2 = QString(),
                                         const QString &str3 = QString(),
                                         const QString &str4 = QString(),
                                         const QString &str5 = QString());

BUTTER_EXPORT void setVerticalScrollMode(QAbstractItemView *tw);

BUTTER_EXPORT void setCheckedWithoutSignals(QAbstractButton *button, bool checked);

struct BUTTER_EXPORT SizePolicyMinMax
{
    QSizePolicy sizePolicy;
    int min;
    int max;

    void restoreWidth(QWidget *widget) const;
    void restoreHeight(QWidget *widget) const;
};

BUTTER_EXPORT SizePolicyMinMax forceWidth(QWidget *widget, int width);
BUTTER_EXPORT SizePolicyMinMax forceHeight(QWidget *widget, int height);

BUTTER_EXPORT int getMaxFullyDisplayedLines(QTextEdit *textEdit);
BUTTER_EXPORT int getMaxFullyDisplayedLines(QPlainTextEdit *plainTextEdit);

BUTTER_EXPORT QByteArray applyColorToSvg(const QByteArray &data, QColor color);
BUTTER_EXPORT QByteArray applyColorToSvg(const QString &filename, QColor color);

/**
 * @brief Finds the theme-specific icon path and calls `setter` functor providing a pointer of an
 * object which has to be used and loaded icon
 * @param supportedIconsNames list of <object ptr, icon name>
 * @param setter functor which has to be called
 *   for example we need to set an action icon, the functor can be just [](void* o, const QIcon
 * &icon) { static_cast<QAction*>(o)->setIcon(icon); }
 */
BUTTER_EXPORT void setThemeIcons(const QList<QPair<void *, QString>> &supportedIconsNames,
                                 const std::function<void(void *, const QIcon &)> &setter);

BUTTER_EXPORT void prependQAction(QAction *action, QMenu *menu);
BUTTER_EXPORT qreal devicePixelRatio(const QPaintDevice *p);
/**
 * @brief Select comboBox item by value in Qt::UserRole.
 * @param comboBox
 * @param data - value to search in combobox item data
 * @param defaultIndex - item to select in case no match
 */
BUTTER_EXPORT void selectIndexByData(QComboBox *comboBox, const QVariant &data,
                                     int defaultIndex = -1);
/**
 * @brief Emit data change signal in a model's column (DisplayRole)
 * @param model - model containing data with changes
 * @param column - column in the model
 */
BUTTER_EXPORT void emitColumnChanged(QAbstractItemModel *model, int column);

BUTTER_EXPORT bool filterStringContains(const QString &string, const QSortFilterProxyModel *model);

#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
using ColorFloat = float;
using KeyComb = QKeyCombination;
#else
using ColorFloat = qreal;
using KeyComb = int;
#endif

BUTTER_EXPORT QPointF mouseEventPos(QMouseEvent *ev);
BUTTER_EXPORT QPoint mouseEventGlobalPos(QMouseEvent *ev);

} // qhelpers

#endif // HELPERS_H
