#include "core/ClutterJson.h"

ClutterJson ClutterJson::last() const
{
    if (!hasChildren()) {
        return ClutterJson();
    }

    const RzJson *last = value->children.first;
    while (last->next) {
        last = last->next;
    }

    return ClutterJson(last, owner);
}

QStringList ClutterJson::keys() const
{
    QStringList list;

    if (value && value->type == RZ_JSON_OBJECT) {
        for (const RzJson *child = value->children.first; child; child = child->next) {
            list.append(child->key);
        }
    }

    return list;
}
