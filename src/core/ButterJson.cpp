#include "core/ButterJson.h"

ButterJson ButterJson::last() const
{
    if (!hasChildren()) {
        return ButterJson();
    }

    const RzJson *last = value->children.first;
    while (last->next) {
        last = last->next;
    }

    return ButterJson(last, owner);
}

QStringList ButterJson::keys() const
{
    QStringList list;

    if (value && value->type == RZ_JSON_OBJECT) {
        for (const RzJson *child = value->children.first; child; child = child->next) {
            list.append(child->key);
        }
    }

    return list;
}
