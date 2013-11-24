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

# TODO: objects will be gone in py3k? Investigate
def walk_parents(parents, bases=("Document", "EmDocument", "type", "object")):
  """Walks through the parents and return each parent class object.

  Returns until the name of the classes specified in `bases`.
  Implemented using Wikipedia's BFS pseudocode.

  Args:
    p: The list of direct parents of a class object
    bases: The name of the classes that's considered to be the ones that should
           not be included and also terminates when encountered. defaults to
           ("Document", "type", "object")

  Returns:
    A list of all the parents ordered via BFS. This means the first element is
    the immediate parent..
  """

  frontier = parents
  next_clses = []
  all_parents = []
  found = False
  while not found:
    found = True
    for cls in frontier:
      if cls.__name__ not in bases:
        found = False
        if cls not in all_parents:
          all_parents.append(cls)
          # cls.__bases__ are all the parent classes directly above cls
          next_clses.extend(cls.__bases__)
    frontier = next_clses
    next_clses = []
  return all_parents

def mediocre_copy(obj):
  """ Makes a partial deep copy of an object depending on the file type.

      It's kind of like a deep copy, but it only make copies of lists, tuples,
      and dictionaries (and other primitive types). Other complex object such as
      ones you created are kept as references.

      Arg:
        obj: Any object.

      Returns:
        A meh copy of the obj as described.
  """

  if isinstance(obj, list):
    return [mediocre_copy(i) for i in obj]
  if isinstance(obj, tuple):
    return tuple(mediocre_copy(i) for i in obj)
  if isinstance(obj, dict):
    return dict(mediocre_copy(i) for i in obj.iteritems())

  return obj
