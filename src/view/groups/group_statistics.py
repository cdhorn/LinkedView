#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2022       Christopher Horn
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
StatisticsCardGroup
"""

# ------------------------------------------------------------------------
#
# Plugin Modules
#
# ------------------------------------------------------------------------
from ..cards.card_text import TextCard
from .group_list import CardGroupList


# ------------------------------------------------------------------------
#
# StatisticsCardGroup Class
#
# ------------------------------------------------------------------------
class StatisticsCardGroup(CardGroupList):
    """
    The StatisticsCardGroup class provides a container for managing
    statistical information about the database.
    """

    def __init__(self, grstate, groptions, title, data):
        CardGroupList.__init__(
            self, grstate, groptions, None, enable_drop=False
        )
        card = TextCard(grstate, groptions, title=title, data=data)
        self.add_card(card)
