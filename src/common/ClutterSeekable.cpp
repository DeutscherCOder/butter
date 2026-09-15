#include "ClutterSeekable.h"

#include "core/MainWindow.h"

#include <QPlainTextEdit>

ClutterSeekable::ClutterSeekable(QObject *parent) : QObject(parent)
{
    connect(Core(), &ClutterCore::seekChanged, this, &ClutterSeekable::onCoreSeekChanged);
}

ClutterSeekable::~ClutterSeekable() {}

void ClutterSeekable::setSynchronization(bool sync)
{
    synchronized = sync;
    onCoreSeekChanged(Core()->getOffset(), ClutterCore::SeekHistoryType::New);
    emit syncChanged();
}

void ClutterSeekable::onCoreSeekChanged(RVA addr, ClutterCore::SeekHistoryType type)
{
    if (synchronized && widgetOffset != addr) {
        updateSeek(addr, type, true);
    }
}

void ClutterSeekable::updateSeek(RVA addr, ClutterCore::SeekHistoryType type, bool localOnly)
{
    previousOffset = widgetOffset;
    widgetOffset = addr;
    if (synchronized && !localOnly) {
        Core()->seek(addr);
    }

    emit seekableSeekChanged(addr, type);
}

void ClutterSeekable::seekPrev()
{
    if (synchronized) {
        Core()->seekPrev();
    } else {
        this->seek(previousOffset, ClutterCore::SeekHistoryType::Undo);
    }
}

RVA ClutterSeekable::getOffset() const
{
    return (synchronized) ? Core()->getOffset() : widgetOffset;
}

void ClutterSeekable::toggleSynchronization()
{
    setSynchronization(!synchronized);
}

bool ClutterSeekable::isSynchronized() const
{
    return synchronized;
}

void ClutterSeekable::seekToReference(RVA offset)
{
    if (offset == RVA_INVALID) {
        return;
    }

    const QList<XrefDescription> refs = Core()->getXRefs(offset, false, false);

    if (refs.length()) {
        if (refs.length() > 1) {
            qWarning() << tr("More than one (%1) references here. Weird behaviour expected.")
                                  .arg(refs.length());
        }
        // Try first call
        for (auto &ref : refs) {
            if (ref.to != RVA_INVALID && ref.type == "CALL") {
                Core()->seekAndShow(ref.to);
                return;
            }
        }
        // Fallback to first valid, if any
        for (auto &ref : refs) {
            if (ref.to != RVA_INVALID) {
                Core()->seekAndShow(ref.to);
                return;
            }
        }
    }
}
