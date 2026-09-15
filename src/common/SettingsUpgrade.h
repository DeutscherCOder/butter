#ifndef SETTINGS_UPGRADE_H
#define SETTINGS_UPGRADE_H

#include <QSettings>

#include <core/Butter.h>

/**
 * @file SettingsUpgrade.h
 * @brief Logic for migrating and importing Butter settings from older versions
 */

namespace Butter {
void initializeSettings();
/**
 * @brief Check if Butter should offer importing settings from version that can't be directly
 * updated.
 * @return True if this is first time running Butter and r2 based Butter <= 1.12 settings exist.
 */
bool shouldOfferSettingImport();
/**
 * @brief Ask user if Butter should import settings from pre-rizin Butter.
 *
 * This function assume that QApplication isn't running yet.
 */
void showSettingImportDialog(int &argc, char **argv);
void migrateThemes();
}

#endif // SETTINGS_UPGRADE_H
