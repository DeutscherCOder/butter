#include "ButterLayout.h"

using namespace Butter;

bool Butter::isBuiltinLayoutName(const QString &name)
{
    return name == layoutDefault || name == layoutDebug;
}
