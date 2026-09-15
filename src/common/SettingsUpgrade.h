#ifndef SETTINGS_UPGRADE_H
#define SETTINGS_UPGRADE_H

#include <QSettings>

#include <core/Clutter.h>

/**
 * @file SettingsUpgrade.h
 * @brief Logic for migrating and importing Clutter settings from older versions
 */

namespace Clutter {
void initializeSettings();
/**
 * @brief Check if Clutter should offer importing settings from version that can't be directly
 * updated.
 * @return True if this is first time running Clutter and r2 based Clutter <= 1.12 settings exist.
 */
bool shouldOfferSettingImport();
/**
 * @brief Ask user if Clutter should import settings from pre-rizin Clutter.
 *
 * This function assume that QApplication isn't running yet.
 */
void showSettingImportDialog(int &argc, char **argv);
void migrateThemes();
}

#endif // SETTINGS_UPGRADE_H
