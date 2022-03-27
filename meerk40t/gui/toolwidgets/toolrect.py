import wx

from meerk40t.gui.toolwidgets.toolwidget import ToolWidget
from meerk40t.svgelements import Path, Rect


class RectTool(ToolWidget):
    """
    Rectangle Drawing Tool.

    Adds Rectangles with click and drag.
    """

    def __init__(self, scene):
        ToolWidget.__init__(self, scene)
        self.start_position = None
        self.p1 = None
        self.p2 = None

    def process_draw(self, gc: wx.GraphicsContext):
        if self.p1 is not None and self.p2 is not None:
            x0 = min(self.p1.real, self.p2.real)
            y0 = min(self.p1.imag, self.p2.imag)
            x1 = max(self.p1.real, self.p2.real)
            y1 = max(self.p1.imag, self.p2.imag)
            gc.SetPen(self.pen)
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            gc.DrawRectangle(x0, y0, x1 - x0, y1 - y0)

    def event(self, window_pos=None, space_pos=None, event_type=None):
        if event_type == "leftdown":
            self.p1 = complex(space_pos[0], space_pos[1])
        elif event_type == "move":
            self.p2 = complex(space_pos[0], space_pos[1])
            self.scene.request_refresh()
        elif event_type == "leftup":
            try:
                if self.p1 is None:
                    return
                self.p2 = complex(space_pos[0], space_pos[1])
                x0 = min(self.p1.real, self.p2.real)
                y0 = min(self.p1.imag, self.p2.imag)
                x1 = max(self.p1.real, self.p2.real)
                y1 = max(self.p1.imag, self.p2.imag)
                rect = Rect(x0, y0, x1 - x0, y1 - y0, stroke="blue", stroke_width=1000)
                t = Path(rect)
                if len(t) != 0:
                    self.scene.context.elements.add_elem(t, classify=True)
                self.p1 = None
                self.p2 = None
            except IndexError:
                pass