from copy import copy

from meerk40t.core.node.node import Node


class PathNode(Node):
    """
    PathNode is the bootstrapped node type for the 'elem path' type.
    """

    def __init__(self, data_object, **kwargs):
        super(PathNode, self).__init__(data_object)
        data_object.node = self

    def __repr__(self):
        return "PathNode('%s', %s, %s)" % (
            self.type,
            str(self.object),
            str(self._parent),
        )

    def __copy__(self):
        return PathNode(copy(self.object))

    def default_map(self, default_map=None):
        default_map = super(PathNode, self).default_map(default_map=default_map)
        element = self.object
        if self.object is not None:
            default_map.update(self.object.values)
        default_map["element_type"] = "Path"
        default_map["stroke"] = element.stroke
        default_map["fill"] = element.fill
        default_map["stroke-width"] = element.stroke_width
        default_map['transform'] = element.transform
        if default_map.get('id'):
            default_map['id'] = element.id
        return default_map

    def drop(self, drag_node):
        drop_node = self
        # Dragging element into element.
        if drag_node.type.startswith("elem"):
            drop_node.insert_sibling(drag_node)
            return True
        return False

    def revalidate_points(self):
        bounds = self.bounds
        if bounds is None:
            return
        if len(self._points) < 9:
            self._points.extend([None] * (9 - len(self._points)))
        self._points[0] = [bounds[0], bounds[1], "bounds top_left"]
        self._points[1] = [bounds[2], bounds[1], "bounds top_right"]
        self._points[2] = [bounds[0], bounds[3], "bounds bottom_left"]
        self._points[3] = [bounds[2], bounds[3], "bounds bottom_right"]
        cx = (bounds[0] + bounds[2]) / 2
        cy = (bounds[1] + bounds[3]) / 2
        self._points[4] = [cx, cy, "bounds center_center"]
        self._points[5] = [cx, bounds[1], "bounds top_center"]
        self._points[6] = [cx, bounds[3], "bounds bottom_center"]
        self._points[7] = [bounds[0], cy, "bounds center_left"]
        self._points[8] = [bounds[2], cy, "bounds center_right"]
        obj = self.object
        if hasattr(obj, "point"):
            if len(self._points) <= 11:
                self._points.extend([None] * (11 - len(self._points)))
            start = obj.point(0)
            end = obj.point(1)
            self._points[9] = [start[0], start[1], "endpoint"]
            self._points[10] = [end[0], end[1], "endpoint"]

    def update_point(self, index, point):
        return False

    def add_point(self, point, index=None):
        return False