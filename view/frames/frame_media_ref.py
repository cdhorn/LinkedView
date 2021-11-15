#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2021      Christopher Horn
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
MediaRefGrampsFrame
"""

# ------------------------------------------------------------------------
#
# Gramps modules
#
# ------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.errors import WindowActiveError
from gramps.gui.editors import EditMediaRef

# ------------------------------------------------------------------------
#
# Plugin modules
#
# ------------------------------------------------------------------------
from ..common.common_utils import menu_item
from .frame_media import MediaGrampsFrame

_ = glocale.translation.sgettext


# ------------------------------------------------------------------------
#
# MediaRefGrampsFrame Class
#
# ------------------------------------------------------------------------
class MediaRefGrampsFrame(MediaGrampsFrame):
    """
    The MediaRefGrampsFrame exposes the image and some facts about Media.
    """

    def __init__(self, grstate, groptions, obj, media_ref):
        media = grstate.fetch("Media", media_ref.ref)
        MediaGrampsFrame.__init__(
            self, grstate, groptions, media, reference_tuple=(obj, media_ref)
        )
        if not groptions.ref_mode:
            return

    def add_ref_custom_actions(self, action_menu):
        """
        Add custom action menu items for the reference.
        """
        action_menu.append(self._edit_media_ref_option())
        action_menu.append(
            menu_item(
                "gramps-media",
                _("Make active media"),
                self._make_active_media,
            )
        )

    def _edit_media_ref_option(self):
        """
        Build the edit option.
        """
        name = "{} {}".format(_("Edit"), _("reference"))
        return menu_item("gtk-edit", name, self.edit_media_ref)

    def edit_media_ref(self, *_dummy_obj):
        """
        Launch the editor.
        """
        try:
            EditMediaRef(
                self.grstate.dbstate,
                self.grstate.uistate,
                [],
                self.primary.obj,
                self.reference.obj,
                self.save_ref,
            )
        except WindowActiveError:
            pass

    def _make_active_media(self, _dummy_var1):
        """
        Make the image the active media item.
        """
        new_list = []
        image_ref = None
        image_handle = self.primary.obj.get_handle()
        for media_ref in self.base.obj.get_media_list():
            if media_ref.ref == image_handle:
                image_ref = media_ref
            else:
                new_list.append(media_ref)
        if image_ref:
            new_list.insert(0, image_ref)

        message = "{} {} {} {} {} {} {}".format(
            _("Set"),
            _("Media"),
            self.primary.obj.get_gramps_id(),
            _("Active"),
            _("for"),
            self.base.obj_type,
            self.base.obj.get_gramps_id(),
        )
        self.base.obj.set_media_list(new_list)
        self.base.commit(self.grstate, message)