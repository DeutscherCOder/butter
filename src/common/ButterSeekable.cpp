#include "ButterSeekable.h"

#include "core/MainWindow.h"

#include <QPlainTextEdit>

ButterSeekable::ButterSeekable(QObject *parent) : QObject(parent)
{
    connect(Core(), &ButterCore::seekChanged, this, &ButterSeekable::onCoreSeekChanged);
}

ButterSeekable::~ButterSeekable() {}

void ButterSeekable::setSynchronization(bool sync)
{
    synchronized = sync;
    onCoreSeekChanged(Core()->getOffset(), ButterCore::SeekHistoryType::New);
    emit syncChanged();
}

void ButterSeekable::onCoreSeekChanged(RVA addr, ButterCore::SeekHistoryType type)
{
    if (synchronized && widgetOffset != addr) {
        updateSeek(addr, type, true);
    }
}

void ButterSeekable::updateSeek(RVA addr, ButterCore::SeekHistoryType type, bool localOnly)
{
    previousOffset = widgetOffset;
    widgetOffset = addr;
    if (synchronized && !localOnly) {
        Core()->seek(addr);
    }

    emit seekableSeekChanged(addr, type);
}

void ButterSeekable::seekPrev()
{
    if (synchronized) {
        Core()->seekPrev();
    } else {
        this->seek(previousOffset, ButterCore::SeekHistoryType::Undo);
    }
}

RVA ButterSeekable::getOffset() const
{
    return (synchronized) ? Core()->getOffset() : widgetOffset;
}

void ButterSeekable::toggleSynchronization()
{
    setSynchronization(!synchronized);
}

bool ButterSeekable::isSynchronized() const
{
    return synchronized;
}

void ButterSeekable::seekToReference(RVA offset)
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
