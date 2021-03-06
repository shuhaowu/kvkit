# -*- coding: utf-8 -*-
# This file is part of kvkit
#
# kvkit is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# kvkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with kvkit. If not, see <http://www.gnu.org/licenses/>.

"""KvKit: An object mapper for key value stores.

.. moduleauthor:: Shuhao Wu <shuhao@shuhaowu.com>
"""

from __future__ import absolute_import

from .emdocument import EmDocument
from .document import Document
from .properties.standard import *
from .properties.fancy import *
from .exceptions import *
