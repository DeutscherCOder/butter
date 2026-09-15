// SPDX-License-Identifier: GPL-3.0-or-later
//
// Compatibility facade for out-of-tree plugins that were written against
// upstream Cutter. Everything in this tree is named Clutter, but third-party
// plugin sources and their CMakeLists are not part of this repository, so the
// pre-rebrand names stay available as aliases.
//
// Include it (or any of the Cutter*.h shims next to the real headers) and the
// old names work again:
//
//     #include <plugins/CutterPlugin.h>
//     #include <Cutter.h>
//
// See the "Rebrand and compatibility" section of README.md.

#ifndef CUTTER_COMPAT_H
#define CUTTER_COMPAT_H

// The Clutter declarations the aliases below point at. <Clutter.h> is the
// aggregate core header; the rest cover the widgets and plugin interface.
#include <Clutter.h>
#include <Configuration.h>
#include <ClutterLayout.h>
#include <ClutterSearchable.h>
#include <ClutterSeekable.h>
#include <ClutterDockWidget.h>
#include <ClutterGraphView.h>
#include <ClutterTreeView.h>
#include <ClutterPlugin.h>

// ---- macros -------------------------------------------------------------
//
// CutterPlugin is a macro rather than a type alias on purpose: Qt's moc
// resolves Q_INTERFACES() by name and cannot look through a typedef, so a
// plugin saying Q_INTERFACES(CutterPlugin) only builds if moc sees
// Q_INTERFACES(ClutterPlugin) after preprocessing.

#define CUTTER_EXPORT CLUTTER_EXPORT
#define CutterPlugin_iid ClutterPlugin_iid
#define CutterPlugin ClutterPlugin
#define CutterRzListForeach ClutterRzListForeach
#define CutterRzVectorForeach ClutterRzVectorForeach
#define CutterHtDef ClutterHtDef

// ---- namespace ----------------------------------------------------------

// Upstream had free helpers in namespace Cutter (resource paths, settings).
namespace Clutter {}
namespace Cutter = Clutter;

// ---- types --------------------------------------------------------------

using CutterCore = ClutterCore;
using CutterDockWidget = ClutterDockWidget;
using CutterGraphView = ClutterGraphView;
using CutterInterfaceTheme = ClutterInterfaceTheme;
using CutterJson = ClutterJson;
using CutterJsonOwner = ClutterJsonOwner;
// Upstream kept the layout struct inside namespace Cutter, so after the
// rebrand it lives in namespace Clutter. `namespace Cutter = Clutter` below
// already makes `Cutter::CutterLayout` resolve; this alias additionally keeps
// bare `CutterLayout` (no qualifier) working for plugins that used it.
using CutterLayout = Clutter::ClutterLayout;
using CutterSearchableI = ClutterSearchableI;
using CutterSeekable = ClutterSeekable;
using CutterTreeView = ClutterTreeView;

// ---- templates ----------------------------------------------------------

template<typename T> using CutterPVector = ClutterPVector<T>;
template<typename T> using CutterRzList = ClutterRzList<T>;
template<typename T> using CutterRzIter = ClutterRzIter<T>;

#endif // CUTTER_COMPAT_H
