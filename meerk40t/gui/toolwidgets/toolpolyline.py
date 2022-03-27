import wx

from meerk40t.gui.toolwidgets.toolwidget import ToolWidget
from meerk40t.svgelements import Path, Polyline


class PolylineTool(ToolWidget):
    """
    Polyline Drawing Tool.

    Adds polylines with clicks.
    """

    def __init__(self, scene):
        ToolWidget.__init__(self, scene)
        self.start_position = None
        self.point_series = []
        self.mouse_position = None

    def process_draw(self, gc: wx.GraphicsContext):
        if self.point_series:
            gc.SetPen(self.pen)
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            points = list(self.point_series)
            if self.mouse_position is not None:
                points.append(self.mouse_position)
            gc.DrawLines(points)

    def event(self, window_pos=None, space_pos=None, event_type=None):
        if event_type == "leftclick":
            self.point_series.append((space_pos[0], space_pos[1]))
        elif event_type == "rightdown":
            self.point_series = []
            self.mouse_position = None
            self.scene.request_refresh()
        elif event_type == "hover":
            self.mouse_position = space_pos[0], space_pos[1]
            if self.point_series:
                self.scene.request_refresh()
        elif event_type == "doubleclick":
            polyline = Polyline(*self.point_series, stroke="blue", stroke_width=1000)
            t = Path(polyline)
            if len(t) != 0:
                self.scene.context.elements.add_elem(t, classify=True)
            self.point_series = []
            self.mouse_position = None