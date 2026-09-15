#include "ClutterLayout.h"

using namespace Clutter;

bool Clutter::isBuiltinLayoutName(const QString &name)
{
    return name == layoutDefault || name == layoutDebug;
}
