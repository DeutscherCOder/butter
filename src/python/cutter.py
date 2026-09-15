# SPDX-License-Identifier: GPL-3.0-or-later
#
# Compatibility facade for Python plugins written against upstream Cutter.
#
# This fork ships the same API as `clutter`; upstream plugins do
# `import cutter`, so re-export everything under the old module name too.
#
#     import cutter
#     cutter.cmd("pdg")          # still works
#
# See the "Rebrand and compatibility" section of README.md.

from clutter import *          # noqa: F401,F403
from clutter import cmd, cmdj, core  # noqa: F401
