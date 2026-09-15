// SPDX-License-Identifier: GPL-3.0-or-later
//
// Compatibility facade: <plugins/CutterPlugin.h> for plugins written against
// upstream Cutter. The interface itself is ButterPlugin; this header makes the
// old name, and the old Qt interface IID macro, resolve to it.
//
// `CutterPlugin` has to be a macro (see CutterCompat.h): moc resolves
// Q_INTERFACES() by name and does not follow typedefs.
//
// See the "Rebrand and compatibility" section of README.md.

#ifndef CUTTERPLUGIN_H
#define CUTTERPLUGIN_H

#include "ButterPlugin.h"
#include <CutterCompat.h>

#ifndef CutterPlugin
#define CutterPlugin ButterPlugin
#endif

#endif // CUTTERPLUGIN_H
