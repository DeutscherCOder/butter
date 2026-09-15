// SPDX-License-Identifier: GPL-3.0-or-later
//
// Compatibility facade: <plugins/CutterPlugin.h> for plugins written against
// upstream Cutter. The interface itself is ClutterPlugin; this header makes the
// old name, and the old Qt interface IID macro, resolve to it.
//
// `CutterPlugin` has to be a macro (see CutterCompat.h): moc resolves
// Q_INTERFACES() by name and does not follow typedefs.
//
// See the "Rebrand and compatibility" section of README.md.

#ifndef CUTTERPLUGIN_H
#define CUTTERPLUGIN_H

#include "ClutterPlugin.h"
#include <CutterCompat.h>

#ifndef CutterPlugin
#define CutterPlugin ClutterPlugin
#endif

#endif // CUTTERPLUGIN_H
