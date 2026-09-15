#ifndef BUTTER_LAYOUT_H
#define BUTTER_LAYOUT_H

#include <QByteArray>
#include <QMap>
#include <QString>
#include <QVariantMap>

/**
 * @namespace Utilities related to butter layout
 */
namespace Butter {

struct ButterLayout
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
