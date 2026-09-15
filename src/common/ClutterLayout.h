#ifndef CLUTTER_LAYOUT_H
#define CLUTTER_LAYOUT_H

#include <QByteArray>
#include <QMap>
#include <QString>
#include <QVariantMap>

/**
 * @namespace Utilities related to clutter layout
 */
namespace Clutter {

struct ClutterLayout
{
    QByteArray geometry;
    QByteArray state;
    QMap<QString, QVariantMap> viewProperties;
};

const QString layoutDefault = "Default";
const QString layoutDebug = "Debug";

bool isBuiltinLayoutName(const QString &name);

}
#endif
