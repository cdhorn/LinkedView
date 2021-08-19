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
GrampsMediaBarGroup
"""

# ------------------------------------------------------------------------
#
# Python modules
#
# ------------------------------------------------------------------------
import pickle


# ------------------------------------------------------------------------
#
# GTK modules
#
# ------------------------------------------------------------------------
from gi.repository import Gdk, Gtk


# ------------------------------------------------------------------------
#
# Gramps modules
#
# ------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.db import DbTxn
from gramps.gen.lib import Citation, Note, Source
from gramps.gen.utils.thumbnails import get_thumbnail_image
from gramps.gen.utils.file import media_path_full
from gramps.gui.ddtargets import DdTargets
from gramps.gui.editors import EditCitation, EditMediaRef, EditNote
from gramps.gui.utils import open_file_with_default_application
from gramps.gui.selectors import SelectorFactory


# ------------------------------------------------------------------------
#
# Plugin modules
#
# ------------------------------------------------------------------------
from ..frames.frame_base import GrampsFrame
from ..frames.frame_classes import GrampsConfig, GrampsOptions, GrampsImageViewFrame
from ..frames.frame_const import _LEFT_BUTTON, _RIGHT_BUTTON
from ..frames.frame_image import ImageGrampsFrame
from ..frames.frame_utils import (
    button_activated,
    get_gramps_object_type,
    menu_item,
    submenu_item,
    citation_option_text,
    note_option_text,
)

_ = glocale.translation.sgettext


# ------------------------------------------------------------------------
#
# GrampsMediaBarGroup class
#
# ------------------------------------------------------------------------
class GrampsMediaBarGroup(Gtk.ScrolledWindow, GrampsConfig):
    """
    The MediaBarGroup class provides a container for managing a horizontal
    scrollable list of media items for a given primary Gramps object.
    """

    def __init__(self, grstate, groptions, obj):
        Gtk.ScrolledWindow.__init__(self, hexpand=True, vexpand=False)
        groptions = GrampsOptions("")
        GrampsConfig.__init__(self, grstate, groptions)
        self.obj = obj
        self.obj_type, dummy_var1, dummy_var2 = get_gramps_object_type(obj)

        hbox = Gtk.HBox(hexpand=True, vexpand=False, spacing=3)
        viewport = Gtk.Viewport()
        viewport.add(hbox)
        self.add(viewport)
        self.set_policy(hscrollbar_policy=Gtk.PolicyType.AUTOMATIC, vscrollbar_policy=Gtk.PolicyType.NEVER)

        media_list = self.collect_media()
        if media_list:
            if self.grstate.config.get("options.global.media-bar-sort-by-date"):
                media_list.sort(
                    key=lambda x: x[0].get_date_object().get_sort_value()
                )

            size = 0
            if self.grstate.config.get("options.global.media-bar-display-mode") in [3, 4]:
                size = 1

            crop = False
            if self.grstate.config.get("options.global.media-bar-display-mode") in [2, 4]:
                crop = True

            for (media, media_ref) in media_list:
                frame = GrampsMediaBarItem(
                    grstate,
                    groptions,
                    (self.obj, self.obj_type),
                    media,
                    media_ref,
                    size=size,
                    crop=crop
                )
                hbox.pack_start(frame, False, False, 0)
        self.show_all()


    def collect_media(self):
        """
        Helper to collect the media for the current object.
        """
        media_list = []
        self.extract_media(media_list, self.obj)
        return media_list

    def extract_media(self, media_list, obj):
        """
        Helper to extract a set of media references from an object.
        """
        if not hasattr(obj, "media_list"):
            return
        
        obj_type, dummy_var1, dummy_var2 = get_gramps_object_type(obj)
        query_method = self.grstate.dbstate.db.method(
            "get_%s_from_handle", obj_type
        )

        for media_ref in obj.get_media_list():
            media = self.grstate.dbstate.db.get_media_from_handle(
                media_ref.ref
            )
            media_list.append((media, media_ref))



class GrampsMediaBarItem(GrampsFrame):
    """
    A simple class for managing display of a media bar image.
    """

    def __init__(self, grstate, groptions, obj, media, media_ref, size=0, crop=False):
        GrampsFrame.__init__(self, grstate, groptions, media, secondary_obj=media_ref)
        self.set_hexpand(False)
        self.obj, self.obj_type = obj
        if media_ref:
            thumbnail = self.get_thumbnail(media, media_ref, size, crop)
        elif isinstance(media, Media):
            thumbnail = self.get_thumbnail(media, None, size, crop)
        if thumbnail:
            self.frame.add(thumbnail)
            self.eventbox.add(self.frame)
            self.add(self.eventbox)
        self.enable_drop(drag_data_received=self.drag_data_ref_received)
        
    def get_thumbnail(self, media, media_ref, size, crop):
        """
        Get the thumbnail image.
        """
        mobj = media
        if not mobj:
            mobj = self.grstate.dbstate.db.get_media_from_handle(media_ref.ref)
        if mobj and mobj.get_mime_type()[0:5] == "image":
            rectangle = None
            if media_ref and crop:
                rectangle = media_ref.get_rectangle()
            pixbuf = get_thumbnail_image(
                media_path_full(self.grstate.dbstate.db, mobj.get_path()),
                rectangle=rectangle,
                size=size,
            )
            image = Gtk.Image()
            image.set_from_pixbuf(pixbuf)
            return image
        return None

    def view_photo(self):
        """
        Open the image in the default picture viewer.
        """
        photo_path = media_path_full(self.grstate.dbstate.db, self.primary.obj.get_path())
        open_file_with_default_application(photo_path, self.grstate.uistate)

    def drag_data_ref_received(
        self,
        _dummy_widget,
        _dummy_context,
        _dummy_x,
        _dummy_y,
        data,
        _dummy_info,
        _dummy_time,
    ):
        """
        Handle dropped data.
        """
        if data and data.get_data():
            try:
                dnd_type, obj_id, obj_handle, dummy_var1 = pickle.loads(
                    data.get_data()
                )
            except pickle.UnpicklingError:
                return
            if id(self) == obj_id:
                return
            if DdTargets.CITATION_LINK.drag_type == dnd_type:
                self.added_ref_citation(obj_handle)
            elif DdTargets.NOTE_LINK.drag_type == dnd_type:
                self.added_ref_note(obj_handle)

    def route_action(self, obj, event):
        """
        Route the ref related action if the frame was clicked on.
        """
        if button_activated(event, _RIGHT_BUTTON):
            self.build_action_menu(obj, event)
        else:
            if self.grstate.config.get("options.global.media-bar-page-link"):
                self.switch_object(None, None, "Media", self.primary.obj)
            else:
                self.view_photo()

    def build_action_menu(self, _dummy_obj, event):
        """
        Build the action menu for a right click on a reference object.
        """
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            action_menu = Gtk.Menu()
            action_menu.append(self._edit_media_ref_option())
            action_menu.append(
                self._citations_option(
                    self.secondary.obj,
                    self.add_new_ref_citation,
                    self.add_existing_ref_citation,
                    self.remove_ref_citation,
                )
            )
            action_menu.append(
                self._notes_option(
                    self.secondary.obj,
                    self.add_new_ref_note,
                    self.add_existing_ref_note,
                    self.remove_ref_note,
                )
            )
            action_menu.append(self._change_ref_privacy_option())
            action_menu.add(Gtk.SeparatorMenuItem())
            label = Gtk.MenuItem(label=_("Media reference"))
            label.set_sensitive(False)
            action_menu.append(label)

            action_menu.show_all()
            if Gtk.get_minor_version() >= 22:
                action_menu.popup_at_pointer(event)
            else:
                action_menu.popup(
                    None, None, None, None, event.button, event.time
                )

    def _edit_media_ref_option(self):
        """
        Build the edit option.
        """
        name = "{} {}".format(
            _("Edit"), _("reference")
        )
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
                self.secondary.obj,
                self.save_media_ref,
            )
        except WindowActiveError:
            pass

    def save_media_ref(self, media_ref, action_text=None):
        """
        Save the edited object.
        """
        if not media_ref:
            return
        if action_text:
            action = action_text
        else:
            action = "{} {} {} {} {} {} {} {}".format(
                _("Edited"),
                _("MediaRef"),
                _("for"),
                self.obj_type,
                self.obj.get_gramps_id(),
                _("to"),
                self.primary.obj_type,
                self.primary.obj.get_gramps_id(),

            )
        commit_method = self.grstate.dbstate.db.method("commit_%s", self.obj_type)
        with DbTxn(action, self.grstate.dbstate.db) as trans:
            commit_method(self.obj, trans)

    def add_new_ref_citation(self, _dummy_obj):
        """
        Add a new citation.
        """
        citation = Citation()
        source = Source()
        try:
            EditCitation(
                self.grstate.dbstate,
                self.grstate.uistate,
                [],
                citation,
                source,
                self.added_ref_citation,
            )
        except WindowActiveError:
            pass

    def added_ref_citation(self, handle):
        """
        Add the new or existing citation to the current object.
        """
        if handle and self.secondary.obj.add_citation(handle):
            citation = self.grstate.dbstate.db.get_citation_from_handle(handle)
            action = "{} {} {} {} {} {} {} {} {} {} {}".format(
                _("Added"),
                _("Citation"),
                citation.get_gramps_id(),
                _("to"),
                _("MediaRef"),
                _("for"),
                self.obj_type,
                self.obj.get_gramps_id(),
                _("to"),
                self.primary.obj_type,
                self.primary.obj.get_gramps_id(),
            )
            self.save_media_ref(self.secondary.obj, action_text=action)

    def add_existing_ref_citation(self, _dummy_obj):
        """
        Add an existing citation.
        """
        select_citation = SelectorFactory("Citation")
        selector = select_citation(
            self.grstate.dbstate, self.grstate.uistate, []
        )
        selection = selector.run()
        if selection:
            if isinstance(selection, Source):
                try:
                    EditCitation(
                        self.grstate.dbstate,
                        self.grstate.uistate,
                        [],
                        Citation(),
                        selection,
                        callback=self.added_ref_citation,
                    )
                except WindowActiveError:
                    pass
            elif isinstance(selection, Citation):
                try:
                    EditCitation(
                        self.grstate.dbstate,
                        self.grstate.uistate,
                        [],
                        selection,
                        callback=self.added_ref_citation,
                    )
                except WindowActiveError:
                    pass
            else:
                raise ValueError("Selection must be either source or citation")

    def remove_ref_citation(self, _dummy_obj, citation):
        """
        Remove the given citation from the current object.
        """
        if not citation:
            return
        text = citation_option_text(self.grstate.dbstate.db, citation)
        prefix = _(
            "You are about to remove the following citation from this object:"
        )
        extra = _(
            "This removes the reference but does not delete the citation."
        )
        confirm = _("Are you sure you want to continue?")
        if self.confirm_action(
            _("Warning"),
            "{}\n\n<b>{}</b>\n\n{}\n\n{}".format(prefix, text, extra, confirm),
        ):
            action = "{} {} {} {} {} {} {} {} {} {} {}".format(
                _("Removed"),
                _("Citation"),
                citation.get_gramps_id(),
                _("from"),
                _("MediaRef"),
                _("for"),
                self.obj_type,
                self.obj.get_gramps_id(),
                _("to"),
                self.primary.obj_type,
                self.primary.obj.get_gramps_id(),
            )
            self.secondary.obj.remove_citation_references(
                [citation.get_handle()]
            )
            self.save_media_ref(
                self.secondary.obj, action_text=action
            )

    def add_new_ref_note(self, _dummy_obj, content=None):
        """
        Add a new note.
        """
        note = Note()
        if content:
            note.set(content)
        try:
            EditNote(
                self.grstate.dbstate,
                self.grstate.uistate,
                [],
                note,
                self.added_ref_note,
            )
        except WindowActiveError:
            pass

    def added_ref_note(self, handle):
        """
        Add the new or existing note to the current object.
        """
        if handle and self.secondary.obj.add_note(handle):
            note = self.grstate.dbstate.db.get_note_from_handle(handle)
            action = "{} {} {} {} {} {} {} {} {} {} {}".format(
                _("Added"),
                _("Note"),
                note.get_gramps_id(),
                _("to"),
                _("MediaRef"),
                _("for"),
                self.obj_type,
                self.obj.get_gramps_id(),
                _("to"),
                self.primary.obj_type,
                self.primary.obj.get_gramps_id(),
            )
            self.save_media_ref(self.secondary.obj, action_text=action)

    def add_existing_ref_note(self, _dummy_obj):
        """
        Add an existing note.
        """
        select_note = SelectorFactory("Note")
        selector = select_note(self.grstate.dbstate, self.grstate.uistate, [])
        selection = selector.run()
        if selection:
            self.added_ref_note(selection.handle)

    def remove_ref_note(self, _dummy_obj, note):
        """
        Remove the given note from the current object.
        """
        if not note:
            return
        text = note_option_text(note)
        prefix = _(
            "You are about to remove the following note from this object:"
        )
        extra = _("This removes the reference but does not delete the note.")
        confirm = _("Are you sure you want to continue?")
        if self.confirm_action(
            _("Warning"),
            "{}\n\n<b>{}</b>\n\n{}\n\n{}".format(prefix, text, extra, confirm),
        ):
            action = "{} {} {} {} {} {} {} {} {} {} {}".format(
                _("Removed"),
                _("Note"),
                note.get_gramps_id(),
                _("from"),
                _("MediaRef"),
                _("for"),
                self.obj_type,
                self.obj.get_gramps_id(),
                _("to"),
                self.primary.obj_type,
                self.primary.obj.get_gramps_id(),
            )
            self.secondary.obj.remove_note(note.get_handle())
            self.save_media_ref(
                self.secondary.obj, action_text=action
            )

    def _change_ref_privacy_option(self):
        """
        Build privacy option based on current object state.
        """
        if self.secondary.obj.private:
            return menu_item(
                "gramps-unlock",
                _("Make public"),
                self.change_ref_privacy,
                False,
            )
        return menu_item(
            "gramps-lock", _("Make private"), self.change_ref_privacy, True
        )

    def change_ref_privacy(self, _dummy_obj, mode):
        """
        Update the privacy indicator for the current object.
        """
        if mode:
            text = _("Private")
        else:
            text = _("Public")
        action = "{} {} {} {} {} {} {}".format(
            _("Made"),
            _("MediaRef"),
            self.primary.obj.get_gramps_id(),
            _("for"),
            self.obj_type,
            self.obj.get_gramps_id(),
            text,
        )
        commit_method = self.grstate.dbstate.db.method("commit_%s", self.obj_type)        
        with DbTxn(action, self.grstate.dbstate.db) as trans:
            for media_ref in self.obj.get_media_list():
                if media_ref.ref == self.secondary.obj.ref:
                    media_ref.set_privacy(mode)
                    break
            commit_method(self.obj, trans)