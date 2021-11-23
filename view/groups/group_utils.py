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
Routines to prepare object groups
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
from gramps.gen.lib import Person, Family

# ------------------------------------------------------------------------
#
# Plugin modules
#
# ------------------------------------------------------------------------
from ..common.common_classes import GrampsOptions
from ..frames.frame_couple import CoupleGrampsFrame
from .group_children import ChildrenGrampsFrameGroup
from .group_classes import GrampsFrameGroupExpander
from .group_events import EventsGrampsFrameGroup
from .group_generic import GenericGrampsFrameGroup

from .group_const import GRAMPS_GROUPS

_ = glocale.translation.sgettext


def build_group(grstate, group_type, obj, args):
    """
    Generate and return group for a given object.
    """
    if group_type in GRAMPS_GROUPS:
        return build_simple_group(grstate, group_type, obj, args)
    if group_type == "event":
        return get_events_group(grstate, obj)
    if group_type == "parent":
        return get_parents_group(grstate, obj, args)
    if group_type == "spouse":
        return get_spouses_group(grstate, obj, args)
    if group_type == "reference":
        return get_references_group(grstate, obj, args)
    return None


def build_simple_group(grstate, group_type, obj, args):
    """
    Generate and return a simple group for a given object.
    """
    framegroup, single, plural = GRAMPS_GROUPS[group_type]
    if group_type == "timeline":
        groptions = GrampsOptions(
            "".join(("options.timeline.", grstate.page_type))
        )
        groptions.set_context("timeline")
    else:
        groptions = GrampsOptions("".join(("options.group.", group_type)))

    if "sources" in args and args["sources"]:
        single, plural = _("Cited Source"), _("Cited Sources")

    group = framegroup(grstate, groptions, obj)
    if not group or len(group) == 0:
        return None
    if "raw" in args and args["raw"]:
        return group
    return group_wrapper(grstate, groptions, group, (single, plural, None))


def group_wrapper(grstate, groptions, group, title):
    """
    Wrap a frame group widget with an expander.
    """
    group_title = get_group_title(group, title)
    content = GrampsFrameGroupExpander(grstate, groptions)
    content.set_label("".join(("<small><b>", group_title, "</b></small>")))
    content.add(group)
    return content


def get_group_title(group, title):
    """
    Build title for a frame group.
    """
    (single, plural, fixed) = title
    group_title = fixed
    if not group_title:
        if len(group) == 1:
            group_title = " ".join(("1", single))
        else:
            group_title = " ".join((str(len(group)), plural))
    return group_title


def get_children_group(
    grstate,
    family,
    args,
    context="child",
    person=None,
):
    """
    Get the group for all the children in a family unit.
    """
    groptions = GrampsOptions("".join(("options.group.", context)))
    groptions.set_relation(person)
    groptions.set_context(context)
    group = ChildrenGrampsFrameGroup(grstate, groptions, family)
    if not group or len(group) == 0:
        return None
    if "raw" in args and args["raw"]:
        return group
    if context == "parent":
        title_tuple = (_("Sibling"), _("Siblings"), None)
    else:
        title_tuple = (_("Child"), _("Children"), None)
    return group_wrapper(grstate, groptions, group, title_tuple)


def get_family_unit(grstate, family, args, context="family", relation=None):
    """
    Get the group for a family unit.
    """
    groptions = GrampsOptions("".join(("options.group.", context)))
    groptions.set_relation(relation)
    couple = CoupleGrampsFrame(
        grstate,
        groptions,
        family,
    )
    children = get_children_group(
        grstate,
        family,
        args,
        context=context,
        person=relation,
    )
    if children and len(children) > 0:
        couple.pack_start(children, expand=True, fill=True, padding=0)
    return couple


def get_parents_group(grstate, person, args):
    """
    Get the group for all the parents and siblings of a person.
    """
    parents = None
    primary_handle = person.get_main_parents_family_handle()
    if primary_handle:
        elements = Gtk.VBox(spacing=6)
        if "raw" not in args or not args["raw"]:
            groptions = GrampsOptions("options.group.parent")
            groptions.set_context("parent")
            parents = GrampsFrameGroupExpander(
                grstate, groptions, expanded=True, use_markup=True
            )
            parents.set_label(
                "".join(
                    ("<small><b>", _("Parents and Siblings"), "</b></small>")
                )
            )
            parents.add(elements)
        else:
            parents = elements
        family = grstate.fetch("Family", primary_handle)
        group = get_family_unit(
            grstate, family, args, context="parent", relation=person
        )
        elements.add(group)

    for handle in person.parent_family_list:
        if handle != primary_handle:
            family = grstate.fetch("Family", handle)
            group = get_family_unit(
                grstate, family, args, context="parent", relation=person
            )
            elements.add(group)
    return parents


def get_spouses_group(grstate, person, args):
    """
    Get the group for all the spouses and children of a person.
    """
    spouses = None
    for handle in person.family_list:
        if spouses is None:
            elements = Gtk.VBox(spacing=6)
            if "raw" not in args or not args["raw"]:
                groptions = GrampsOptions("options.group.spouse")
                groptions.set_context("spouse")
                spouses = GrampsFrameGroupExpander(
                    grstate, groptions, expanded=True, use_markup=True
                )
                spouses.set_label(
                    "".join(
                        (
                            "<small><b>",
                            _("Spouses and Children"),
                            "</b></small>",
                        )
                    )
                )
                spouses.add(elements)
            else:
                spouses = elements
        family = grstate.fetch("Family", handle)
        group = get_family_unit(
            grstate, family, args, context="spouse", relation=person
        )
        elements.add(group)
    return spouses


def get_references_group(
    grstate,
    obj,
    args,
    groptions=None,
    maximum=0,
    obj_types=None,
    obj_list=None,
    age_base=None,
):
    """
    Get the group of objects that reference the given object.
    """
    if not obj_list:
        obj_list = grstate.dbstate.db.find_backlink_handles(obj.get_handle())
        if not obj_list:
            return None

    total = 0
    tuple_list = []
    handle_cache = []
    if not obj_types:
        for item in obj_list:
            if item[1] not in handle_cache:
                tuple_list.append(item)
                handle_cache.append(item[1])
                total = total + 1
    else:
        for obj_type, handle in obj_list:
            if obj_type in obj_types:
                if handle not in handle_cache:
                    tuple_list.append((obj_type, handle))
                    handle_cache.append(handle)
                    total = total + 1
    del handle_cache
    tuple_list.sort(key=lambda x: x[0])

    not_shown = 0
    if not maximum:
        maximum = grstate.config.get("options.global.max-references-per-group")
    if total > maximum:
        not_shown = total - maximum
        tuple_list = tuple_list[:maximum]

    groptions = groptions or GrampsOptions("options.group.reference")
    groptions.set_age_base(age_base)
    group = GenericGrampsFrameGroup(grstate, groptions, "Tuples", tuple_list)

    single, plural = _("Reference"), _("References")
    if args and "title" in args:
        (single, plural) = args["title"]
    title = get_group_title(group, (single, plural, None))
    if not_shown:
        title = "".join(
            (title, " (", str(not_shown), " ", _("Not Shown"), ")")
        )
    return group_wrapper(grstate, groptions, group, (None, None, title))


def get_events_group(grstate, obj):
    """
    Get the group for all the events related to a person or family
    """
    group_set = Gtk.VBox(spacing=6)
    if isinstance(obj, Person):
        group = prepare_event_group(grstate, obj, "Person")
        if group:
            group_set.add(group)

        for handle in obj.get_family_handle_list():
            family = grstate.fetch("Family", handle)
            group = prepare_event_group(grstate, family, "Family")
            if group:
                group_set.add(group)
    elif isinstance(obj, Family):
        group = prepare_event_group(grstate, obj, "Family")
        if group:
            group_set.add(group)
    return group_set


def prepare_event_group(grstate, obj, obj_type):
    """
    Prepare and return an event group for use in a group set.
    """
    if not obj.get_event_ref_list():
        return None

    groptions = GrampsOptions("options.group.event")
    groptions.set_context("event")
    group = EventsGrampsFrameGroup(grstate, groptions, obj)
    elements = Gtk.VBox(spacing=6)
    elements.add(group)

    if obj_type == "Person":
        event_type = _("Personal")
    else:
        event_type = _("Family")

    if len(group) == 1:
        title = " ".join(("1", event_type, _("Event")))
    else:
        title = " ".join((str(len(group)), event_type, _("Events")))
    return group_wrapper(grstate, groptions, elements, (None, None, title))
