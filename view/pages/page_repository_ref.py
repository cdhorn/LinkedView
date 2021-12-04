# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2001-2007  Donald N. Allingham
# Copyright (C) 2008       Raphael Ackermann
# Copyright (C) 2009-2010  Gary Burton
# Copyright (C) 2010       Benny Malengier
# Copyright (C) 2012       Doug Blank <doug.blank@gmail.com>
# Copyright (C) 2015-2016  Nick Hall
# Copyright (C) 2015       Serge Noiraud
# Copyright (C) 2021       Christopher Horn
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
RepoRef Profile Page
"""

# -------------------------------------------------------------------------
#
# GTK/Gnome modules
#
# -------------------------------------------------------------------------
from gi.repository import Gtk

# -------------------------------------------------------------------------
#
# Gramps Modules
#
# -------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale

# -------------------------------------------------------------------------
#
# Plugin Modules
#
# -------------------------------------------------------------------------
from ..common.common_classes import GrampsOptions
from ..frames.frame_repository_ref import RepositoryRefGrampsFrame
from ..frames.frame_source import SourceGrampsFrame
from .page_base import BaseProfilePage

_ = glocale.translation.sgettext


class RepositoryRefProfilePage(BaseProfilePage):
    """
    Provides the repository reference profile page view with information
    about the repository a source is located in.
    """

    def __init__(self, dbstate, uistate, config, callbacks):
        BaseProfilePage.__init__(self, dbstate, uistate, config, callbacks)
        self.active_profile = None

    @property
    def obj_type(self):
        """
        Primary object type underpinning the page.
        """
        return "Source"

    @property
    def page_type(self):
        """
        Page type.
        """
        return "RepoRef"

    def render_page(self, header, vbox, context):
        """
        Render the page contents.
        """
        if not context:
            return

        source = context.primary_obj.obj
        repo_ref = context.reference_obj.obj

        groptions = GrampsOptions("options.active.source")
        source_frame = SourceGrampsFrame(
            self.grstate,
            groptions,
            source,
        )
        groptions = GrampsOptions("options.active.repository")
        groptions.set_backlink(source.get_handle())
        groptions.set_ref_mode(2)
        self.active_profile = RepositoryRefGrampsFrame(
            self.grstate, groptions, source, repo_ref
        )
        focal = self.wrap_focal_widget(self.active_profile)

        vheader = Gtk.VBox()
        if focal == self.active_profile:
            vheader.set_spacing(3)
        vheader.pack_start(source_frame, False, False, 0)
        vheader.pack_start(focal, False, False, 0)

        groups = self.config.get("options.page.reporef.layout.groups").split(
            ","
        )
        obj_groups = self.get_object_groups(groups, repo_ref)
        body = self.render_group_view(obj_groups)

        if self.config.get("options.global.pin-header"):
            header.pack_start(vheader, False, False, 0)
            header.show_all()
        else:
            vbox.pack_start(vheader, False, False, 0)
        vbox.pack_start(body, True, True, 0)
        vbox.show_all()
