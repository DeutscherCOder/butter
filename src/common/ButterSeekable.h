#pragma once

#include "core/Butter.h"

class MainWindow;

/**
 * @brief Class to synchronize seeks with other widgets
 */
class BUTTER_EXPORT ButterSeekable : public QObject
{
    Q_OBJECT

public:
    explicit ButterSeekable(QObject *parent = nullptr);
    ~ButterSeekable();

    /**
     * @brief seek changes current offset.
     * If the seekable is synchronized with Core, then
     * the Core offset will be modified and then the ButterCore::seekChanged
     * signal will be emitted.
     * In any case, ButterSeekable::seekableSeekChanged is emitted.
     * @param addr the location to seek at.
     * @param type the type of seek wrt history (Undo, Redo, or New)
     */
    void seek(RVA addr, ButterCore::SeekHistoryType type = ButterCore::SeekHistoryType::New)
    {
        updateSeek(addr, type, false);
    }

    /**
     * @brief setSynchronization sets
     * Core seek synchronization.
     */
    void setSynchronization(bool sync);

    /**
     * @brief getOffset returns the seekable offset.
     * If the seekable is synchronized with Core, this function
     * is similar to Core()->getOffset.
     * If it's not synchronized, it will return the seekable current seek.
     * @return the seekable current offset.
     */
    RVA getOffset() const;

    /**
     * @brief isSynchronized tells whether the seekable
     * is synchronized with Core or not.
     * @return true if synchronized, false otherwise
     */
    bool isSynchronized() const;

    /**
     * @brief seekToReference will seek to the function or the object which is referenced in a given
     * offset
     * @param offset An address that contains a reference to jump to
     */
    void seekToReference(RVA offset);

public slots:
    /**
     * @brief seekPrev seeks to last location.
     */
    void seekPrev();

    /**
     * @brief toggleSyncWithCore toggles Core seek synchronization.
     */
    void toggleSynchronization();

private slots:
    void onCoreSeekChanged(RVA addr, ButterCore::SeekHistoryType type);

private:
    /**
     * @brief widgetOffset widget seek location.
     */
    RVA widgetOffset = RVA_INVALID;

    /**
     * @brief previousOffset last seek location.
     * @todo maybe use an actual history?
     */
    RVA previousOffset = RVA_INVALID;

    /**
     * @brief synchronized tells with the seekable's offset is
     * synchronized with core or not.
     */
    bool synchronized = true;

    /**
     * @brief internal method for changing the seek
     * @param localOnly whether the seek should be updated globally if synchronized
     */
    void updateSeek(RVA addr, ButterCore::SeekHistoryType type, bool localOnly);

signals:
    void seekableSeekChanged(RVA addr, ButterCore::SeekHistoryType type);
    void syncChanged();
};
