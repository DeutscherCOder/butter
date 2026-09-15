// SPDX-License-Identifier: GPL-3.0-or-later
//
// Compatibility facade for out-of-tree plugins that were written against
// upstream Cutter. Everything in this tree is named Butter, but third-party
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

// The Butter declarations the aliases below point at. <Butter.h> is the
// aggregate core header; the rest cover the widgets and plugin interface.
#include <Butter.h>
#include <Configuration.h>
#include <ButterLayout.h>
#include <ButterSearchable.h>
#include <ButterSeekable.h>
#include <ButterDockWidget.h>
#include <ButterGraphView.h>
#include <ButterTreeView.h>
#include <ButterPlugin.h>

// ---- macros -------------------------------------------------------------
//
// CutterPlugin is a macro rather than a type alias on purpose: Qt's moc
// resolves Q_INTERFACES() by name and cannot look through a typedef, so a
// plugin saying Q_INTERFACES(CutterPlugin) only builds if moc sees
// Q_INTERFACES(ButterPlugin) after preprocessing.

#define CUTTER_EXPORT BUTTER_EXPORT
#define CutterPlugin_iid ButterPlugin_iid
#define CutterPlugin ButterPlugin
#define CutterRzListForeach ButterRzListForeach
#define CutterRzVectorForeach ButterRzVectorForeach
#define CutterHtDef ButterHtDef

// ---- namespace ----------------------------------------------------------

// Upstream Cutter had free helpers in namespace Cutter (resource paths,
// settings). Butter keeps them in namespace Butter.
namespace Butter {}
namespace Cutter = Butter;

// ---- types --------------------------------------------------------------

using CutterCore = ButterCore;
using CutterDockWidget = ButterDockWidget;
using CutterGraphView = ButterGraphView;
using CutterInterfaceTheme = ButterInterfaceTheme;
using CutterJson = ButterJson;
using CutterJsonOwner = ButterJsonOwner;
// Upstream kept the layout struct inside namespace Cutter, so in Butter it
// lives in namespace Butter. `namespace Cutter = Butter` above already makes
// `Cutter::CutterLayout` resolve; this alias additionally keeps bare
// `CutterLayout` (no qualifier) working for plugins that used it.
using CutterLayout = Butter::ButterLayout;
using CutterSearchableI = ButterSearchableI;
using CutterSeekable = ButterSeekable;
using CutterTreeView = ButterTreeView;

// ---- templates ----------------------------------------------------------

template<typename T> using CutterPVector = ButterPVector<T>;
template<typename T> using CutterRzList = ButterRzList<T>;
template<typename T> using CutterRzIter = ButterRzIter<T>;

#endif // CUTTER_COMPAT_H
