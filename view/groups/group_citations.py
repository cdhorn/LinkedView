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
CitationsGrampsFrameGroup
"""

# ------------------------------------------------------------------------
#
# GTK modules
#
# ------------------------------------------------------------------------
from gi.repository import Gtk


# ------------------------------------------------------------------------
#
# Gramps modules
#
# ------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.db import DbTxn


# ------------------------------------------------------------------------
#
# Plugin modules
#
# ------------------------------------------------------------------------
from ..frames.frame_citation import CitationGrampsFrame
from ..frames.frame_utils import get_gramps_object_type
from .group_list import GrampsFrameGroupList

_ = glocale.translation.sgettext


# ------------------------------------------------------------------------
#
# CitationsGrampsFrameGroup class
#
# ------------------------------------------------------------------------
class CitationsGrampsFrameGroup(GrampsFrameGroupList):
    """
    The CitationsGrampsFrameGroup class provides a container for viewing and
    managing all of the citations associated with a primary Gramps object.
    """

    def __init__(self, grstate, obj):
        GrampsFrameGroupList.__init__(self, grstate)
        self.obj = obj
        self.obj_type, dummy_var1, dummy_var2 = get_gramps_object_type(obj)
        self.maximum = grstate.config.get(
            "options.global.max-citations-per-group"
        )
        if not self.option("layout", "tabbed"):
            self.hideable = self.option("layout.citation", "hideable")

        groups = {
            "data": Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL),
            "metadata": Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL),
            "image": Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL),
        }
        citation_list = self.collect_citations()

        if citation_list:
            if self.option("citation", "sort-by-date"):
                citation_list.sort(
                    key=lambda x: x[0].get_date_object().get_sort_value()
                )

            for citation, references, ref_type, ref_desc in citation_list:
                reference = (references, ref_type, ref_desc)
                frame = CitationGrampsFrame(
                    grstate,
                    "citation",
                    citation,
                    groups=groups,
                    reference=reference,
                )
                self.add_frame(frame)
        self.show_all()

    def save_new_object(self, handle, insert_row):
        """
        Add new citation to the list.
        """
        citation = self.grstate.dbstate.db.get_citation_from_handle()
        action = "{} {} {} {}".format(
            _("Added Citation"),
            citation.get_gramps_id(),
            _("to"),
            self.obj.get_gramps_id(),
        )
        commit_method = self.grstate.dbstate.db.method(
            "commit_%s", self.obj_type
        )
        with DbTxn(action, self.grstate.dbstate.db) as trans:
            if self.obj.add_citation(handle):
                commit_method(self.obj, trans)

    def collect_citations(self):
        """
        Helper to collect the citation data for the current object.
        """
        citation_list = []
        self.extract_citations(
            0, self.obj_type, citation_list, None, [self.obj]
        )

        if self.obj_type == "Person":
            if self.option("citation", "include-indirect"):
                self.extract_citations(
                    1,
                    _("Primary Name"),
                    citation_list,
                    None,
                    [self.obj.primary_name],
                )
                self.extract_citations(
                    1, _("Media"), citation_list, self.obj.get_media_list
                )
                self.extract_citations(
                    1,
                    _("Alternate Name"),
                    citation_list,
                    self.obj.get_alternate_names,
                )
                self.extract_citations(
                    1, _("Address"), citation_list, self.obj.get_address_list
                )
                self.extract_citations(
                    1,
                    _("Attribute"),
                    citation_list,
                    self.obj.get_attribute_list,
                )
                self.extract_citations(
                    1, _("LDS Event"), citation_list, self.obj.get_lds_ord_list
                )
                self.extract_citations(
                    1,
                    _("Association"),
                    citation_list,
                    self.obj.get_person_ref_list,
                )
                self.extract_citations(
                    1, _("Event"), citation_list, self.obj.get_event_ref_list
                )

            if self.option("citation", "include-family"):
                for family_handle in self.obj.get_family_handle_list():
                    family = self.grstate.dbstate.db.get_family_from_handle(
                        family_handle
                    )
                    self.extract_citations(
                        0, "Family", citation_list, None, [family]
                    )
                    if self.option("citation", "include-family-indirect"):
                        self.extract_family_indirect_citations(
                            citation_list, family
                        )

            if self.option("citation", "include-parent-family"):
                for family_handle in self.obj.get_parent_family_handle_list():
                    family = self.grstate.dbstate.db.get_family_from_handle(
                        family_handle
                    )
                    for child_ref in family.get_child_ref_list():
                        if child_ref.ref == self.obj.get_handle():
                            for handle in child_ref.get_citation_list():
                                citation = self.grstate.dbstate.db.get_citation_from_handle(
                                    handle
                                )
                                citation_list.append(
                                    (
                                        citation,
                                        [child_ref],
                                        1,
                                        _("Parent Family Child"),
                                    )
                                )

        if self.obj_type == "Family":
            if self.option("citation", "include-indirect"):
                self.extract_family_indirect_citations(citation_list, self.obj)

        if self.obj_type == "Source":
            for (
                obj_type,
                obj_handle,
            ) in self.grstate.dbstate.db.find_backlink_handles(
                self.obj.get_handle()
            ):
                if obj_type == "Citation":
                    citation = self.grstate.dbstate.db.get_citation_from_handle(
                        obj_handle
                    )
                    citation_list.append((citation, [self.obj], 0, obj_type))
                    if len(citation_list) >= self.maximum:
                        break

        return citation_list

    def extract_citations(
        self,
        ref_type,
        ref_desc,
        citation_list,
        query_method=None,
        obj_list=None,
    ):
        """
        Helper to extract a set of citations from an object.
        """

        if query_method:
            data = query_method()
        else:
            data = obj_list or []
        for item in data:
            if hasattr(item, "citation_list"):
                for handle in item.get_citation_list():
                    citation = self.grstate.dbstate.db.get_citation_from_handle(
                        handle
                    )
                    citation_list.append((citation, [item], ref_type, ref_desc))
                    if len(citation_list) >= self.maximum:
                        break

    def extract_family_indirect_citations(self, citation_list, family):
        """
        Helper to extract indirect citations for a family.
        """
        self.extract_citations(
            1, _("Family Media"), citation_list, family.get_media_list
        )
        self.extract_citations(
            1, _("Family Attribute"), citation_list, family.get_attribute_list
        )
        self.extract_citations(
            1, _("Family LDS Event"), citation_list, family.get_lds_ord_list
        )
        self.extract_citations(
            1, _("Family Child"), citation_list, family.get_child_ref_list
        )
        self.extract_citations(
            1, _("Family Event"), citation_list, family.get_event_ref_list
        )