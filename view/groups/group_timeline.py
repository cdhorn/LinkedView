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
TimelineGrampsFrameGroup
"""

# ------------------------------------------------------------------------
#
# Gramps modules
#
# ------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale

# ------------------------------------------------------------------------
#
# Plugin modules
#
# ------------------------------------------------------------------------
from ..common.common_utils import get_key_person_events
from ..frames.frame_address import AddressGrampsFrame
from ..frames.frame_citation import CitationGrampsFrame
from ..frames.frame_event_ref import EventRefGrampsFrame
from ..frames.frame_media import MediaGrampsFrame
from ..frames.frame_name import NameGrampsFrame
from ..frames.frame_ordinance import LDSOrdinanceGrampsFrame
from ..timeline import EVENT_CATEGORIES, RELATIVES, Timeline
from .group_list import GrampsFrameGroupList

_ = glocale.translation.sgettext


# ------------------------------------------------------------------------
#
# TimelineGrampsFrameGroup
#
# ------------------------------------------------------------------------
class TimelineGrampsFrameGroup(GrampsFrameGroupList):
    """
    The TimelineGrampsFrameGroup generates an event timeline for a person
    that may also optionally include events for close family if choosen.
    """

    def __init__(self, grstate, groptions, obj):
        GrampsFrameGroupList.__init__(
            self, grstate, groptions, obj, enable_drop=False
        )
        self.options = {
            "categories": [],
            "relations": [],
            "relation_categories": [],
            "ancestors": 1,
            "offspring": 1,
        }
        if not self.get_layout("tabbed"):
            self.hideable = self.get_layout("hideable")

        self.prepare_options()

        self.timeline = Timeline(
            grstate.dbstate.db,
            events=self.options["categories"],
            relatives=self.options["relations"],
            relative_events=self.options["relation_categories"],
        )
        if self.group_base.obj_type == "Person":
            self.timeline.set_person(
                obj.get_handle(),
                ancestors=self.options["ancestors"],
                offspring=self.options["offspring"],
            )
        elif self.group_base.obj_type == "Family":
            self.timeline.set_family(
                obj.get_handle(),
                ancestors=self.options["ancestors"],
                offspring=self.options["offspring"],
            )

        timeline = []
        for (sortval, item) in self.timeline.events(raw=True):
            timeline.append((sortval, "event", None, item))

        if not groptions.age_base and self.group_base.obj_type == "Person":
            if self.get_option("show-age"):
                key_events = get_key_person_events(
                    grstate.dbstate.db, obj, birth_only=True
                )
                if key_events["birth"] and key_events["birth"].date:
                    self.groptions.set_age_base(key_events["birth"].date)

        timeline = self.extract_objects(timeline)
        try:
            groptions.set_ref_mode(
                self.grstate.config.get(
                    "".join(
                        (
                            "options.timeline.",
                            self.group_base.obj_type.lower(),
                            ".reference-mode",
                        )
                    )
                )
            )
        except AttributeError:
            groptions.set_ref_mode(0)

        if self.group_base.obj_type == "Person":
            groptions.set_relation(obj)

        timeline.sort(key=lambda x: x[0])
        for (sortval, timeline_obj_type, timeline_obj, item) in timeline:
            if timeline_obj_type == "event":
                (
                    dummy_event,
                    event_ref,
                    event_person,
                    event_family,
                    dummy_relation,
                    dummy_category,
                ) = item
                obj = event_person
                if event_family:
                    obj = event_family
                self.add_frame(
                    EventRefGrampsFrame(
                        grstate,
                        groptions,
                        obj,
                        event_ref,
                    )
                )
            elif timeline_obj_type == "media":
                (media, dummy_media_ref) = item
                self.add_frame(MediaGrampsFrame(grstate, groptions, media))
            elif timeline_obj_type == "address":
                self.add_frame(
                    AddressGrampsFrame(
                        grstate,
                        groptions,
                        timeline_obj,
                        item,
                    )
                )
            elif timeline_obj_type == "name":
                self.add_frame(
                    NameGrampsFrame(
                        grstate,
                        groptions,
                        timeline_obj,
                        item,
                    )
                )
            elif timeline_obj_type == "citation":
                self.add_frame(
                    CitationGrampsFrame(
                        grstate,
                        groptions,
                        item,
                    )
                )
            elif timeline_obj_type == "ldsord":
                self.add_frame(
                    LDSOrdinanceGrampsFrame(
                        grstate,
                        groptions,
                        timeline_obj,
                        item,
                    )
                )
        self.show_all()

    def prepare_options(self):
        """
        Parse and prepare filter groups and options.
        """
        for category in EVENT_CATEGORIES:
            if self.get_option("".join(("show-class-", category))):
                self.options["categories"].append(category)
            if self.group_base.obj_type == "Person":
                if self.get_option("".join(("show-family-class-", category))):
                    self.options["relation_categories"].append(category)

        if self.group_base.obj_type == "Person":
            for relation in RELATIVES:
                if self.get_option("".join(("show-family-", relation))):
                    self.options["relations"].append(relation)

        self.options["ancestors"] = self.get_option("generations-ancestors")
        self.options["offspring"] = self.get_option("generations-offspring")

    def extract_objects(self, timeline):
        """
        Examine and extract other objects to add to timeline if needed.
        """
        if self.get_option("include-addresses"):
            timeline = timeline + self.extract_object_type("addresses")
        if self.get_option("include-citations"):
            timeline = timeline + self.extract_object_type("citations")
        if self.get_option("include-media"):
            timeline = timeline + self.extract_object_type("media")
        if self.get_option("include-names"):
            timeline = timeline + self.extract_object_type("names")
        if self.get_option("include-ldsords"):
            timeline = timeline + self.extract_object_type("ldsords")
        return timeline

    def extract_object_type(self, extract_type):
        """
        Extract objects if they have an associated date.
        """
        if extract_type == "names":
            extract = extract_names
        elif extract_type == "addresses":
            extract = extract_addresses
        elif extract_type == "media":
            extract = self.extract_media
        elif extract_type == "citations":
            extract = self.extract_citations
        elif extract_type == "ldsords":
            extract = extract_ordinances

        obj_list = []
        if self.group_base.obj_type == "Person":
            obj_list = extract(self.group_base.obj)
        elif self.group_base.obj_type == "Family":
            if self.group_base.obj.get_mother_handle():
                mother = self.fetch(
                    "Person", self.group_base.obj.get_mother_handle()
                )
                obj_list = obj_list + extract(mother)
            if self.group_base.obj.get_father_handle():
                father = self.fetch(
                    "Person", self.group_base.obj.get_father_handle()
                )
                obj_list = obj_list + extract(father)
            if self.group_base.obj.get_child_ref_list():
                for child_ref in self.group_base.obj.get_child_ref_list():
                    child = self.fetch("Person", child_ref.ref)
                    obj_list = obj_list + extract(child)
        return obj_list

    def extract_citations(self, obj):
        """
        Return list of citations with a date value.
        """
        citations = []
        for handle in obj.get_citation_list():
            citation = self.fetch("Citation", handle)
            date = citation.get_date_object()
            if date and date.is_valid() and date.get_sort_value():
                citations.append(
                    (date.get_sort_value(), "citation", obj, citation)
                )
        return citations

    def extract_media(self, obj):
        """
        Return list of media items with a date value.
        """
        media = []
        for media_ref in obj.get_media_list():
            item = self.fetch("Media", media_ref.ref)
            date = item.get_date_object()
            if date and date.is_valid() and date.get_sort_value():
                media.append(
                    (date.get_sort_value(), "media", obj, (item, media_ref))
                )
        return media


def extract_addresses(obj):
    """
    Return list of addresses with a date value.
    """
    addresses = []
    for address in obj.get_address_list():
        date = address.get_date_object()
        if date and date.is_valid() and date.get_sort_value():
            addresses.append((date.get_sort_value(), "address", obj, address))
    return addresses


def extract_names(obj):
    """
    Return list of names with a date value.
    """
    names = []
    for name in obj.get_alternate_names():
        date = name.get_date_object()
        if date and date.is_valid() and date.get_sort_value():
            names.append((date.get_sort_value(), "name", obj, name))
    return names


def extract_ordinances(obj):
    """
    Return list of ordinance items with a date value.
    """
    ordinances = []
    for ordinance in obj.get_lds_ord_list():
        date = ordinance.get_date_object()
        if date and date.is_valid() and date.get_sort_value():
            ordinances.append(
                (date.get_sort_value(), "ldsord", obj, ordinance)
            )
    return ordinances
