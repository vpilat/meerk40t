"""
Mixin functions for wxMeerk40t
"""
import platform
from typing import List

import wx
from wx.lib.scrolledpanel import ScrolledPanel as SP

from meerk40t.core.units import Angle, Length

_ = wx.GetTranslation


def create_menu_for_choices(gui, choices: List[dict]) -> wx.Menu:
    """
    Creates a menu for a given choices table

    Processes submenus, references, radio_state as needed.
    """
    menu = wx.Menu()
    submenus = {}
    choice = dict()

    def get(key, default=None):
        try:
            return choice[key]
        except KeyError:
            return default

    def execute(choice):
        func = choice["action"]
        func_kwargs = choice["kwargs"]
        func_args = choice["kwargs"]

        def specific(event=None):
            func(*func_args, **func_kwargs)

        return specific

    def set_bool(choice, value):
        obj = choice["object"]
        param = choice["attr"]

        def check(event=None):
            setattr(obj, param, value)

        return check

    for c in choices:
        choice = c
        submenu_name = get("submenu")
        submenu = None
        if submenu_name in submenus:
            submenu = submenus[submenu_name]
        else:
            if get("separate_before", default=False):
                menu.AppendSeparator()
            if submenu_name is not None:
                submenu = wx.Menu()
                menu.AppendSubMenu(submenu, submenu_name)
                submenus[submenu_name] = submenu

        menu_context = submenu if submenu is not None else menu
        t = get("type")
        if t == bool:
            item = menu_context.Append(
                wx.ID_ANY, get("label"), get("tip"), wx.ITEM_CHECK
            )
            obj = get("object")
            param = get("attr")
            check = bool(getattr(obj, param, False))
            item.Check(check)
            gui.Bind(
                wx.EVT_MENU,
                set_bool(choice, not check),
                item,
            )
        elif t == "action":
            item = menu_context.Append(
                wx.ID_ANY, get("label"), get("tip"), wx.ITEM_NORMAL
            )
            gui.Bind(
                wx.EVT_MENU,
                execute(choice),
                item,
            )
        if not submenu and get("separate_after", default=False):
            menu.AppendSeparator()
    return menu


def create_choices_for_node(node, elements) -> List[dict]:
    choices = []

    for func in elements.tree_operations_for_node(node):
        choice = {}
        choices.append(choice)
        choice["action"] = func
        choice["type"] = "action"
        choice["submenu"] = func.submenu
        choice["kwargs"] = dict()
        choice["args"] = tuple()
        choice["separate_before"] = func.separate_before
        choice["separate_after"] = func.separate_after
        choice["label"] = func.name
        choice["real_name"] = func.real_name
        choice["tip"] = func.help
        choice["radio"] = func.radio
        choice["reference"] = func.reference
        choice["user_prompt"] = func.user_prompt
        choice["calcs"] = func.calcs
        choice["values"] = func.values
    return choices


def create_menu_for_node_TEST(gui, node, elements) -> wx.Menu:
    """
    Test code towards unifying choices and tree nodes into choices that parse to menus.

    @param gui:
    @param node:
    @param elements:
    @return:
    """
    choices = create_choices_for_node(node, elements)
    return create_menu_for_choices(gui, choices)


def create_menu_for_node(gui, node, elements, optional_2nd_node=None) -> wx.Menu:
    """
    Create menu for a particular node. Does not invoke the menu.

    Processes submenus, references, radio_state as needed.
    """
    menu = wx.Menu()
    submenus = {}
    radio_check_not_needed = []

    def menu_functions(f, node):
        func_dict = dict(f.func_dict)

        def specific(event=None):
            prompts = f.user_prompt
            for prompt in prompts:
                response = elements.kernel.prompt(prompt["type"], prompt["prompt"])
                if response is None:
                    return
                func_dict[prompt["attr"]] = response
            f(node, **func_dict)

        return specific

    # Check specifically for the optional first (use case: reference nodes)
    if optional_2nd_node is not None:
        mc1 = menu.MenuItemCount
        last_was_separator = False
        for func in elements.tree_operations_for_node(optional_2nd_node):
            submenu_name = func.submenu
            submenu = None
            if submenu_name in submenus:
                submenu = submenus[submenu_name]
            else:
                if submenu_name is not None:
                    last_was_separator = False
                    submenu = wx.Menu()
                    menu.AppendSubMenu(submenu, submenu_name, func.help)
                    submenus[submenu_name] = submenu

            menu_context = submenu if submenu is not None else menu
            if func.separate_before:
                last_was_separator = True
                menu_context.AppendSeparator()
            if func.reference is not None:
                menu_context.AppendSubMenu(
                    create_menu_for_node(
                        gui,
                        func.reference(optional_2nd_node),
                        elements,
                        optional_2nd_node,
                    ),
                    func.real_name,
                )
                continue
            if func.radio_state is not None:
                last_was_separator = False
                item = menu_context.Append(
                    wx.ID_ANY, func.real_name, func.help, wx.ITEM_RADIO
                )
                check = func.radio_state
                item.Check(check)
                if check and menu_context not in radio_check_not_needed:
                    radio_check_not_needed.append(menu_context)
                if func.enabled:
                    gui.Bind(
                        wx.EVT_MENU,
                        menu_functions(func, optional_2nd_node),
                        item,
                    )
                else:
                    item.Enable(False)
            else:
                last_was_separator = False
                if hasattr(func, "check_state") and func.check_state is not None:
                    check = func.check_state
                    kind = wx.ITEM_CHECK
                else:
                    kind = wx.ITEM_NORMAL
                    check = None
                item = menu_context.Append(wx.ID_ANY, func.real_name, func.help, kind)
                if check is not None:
                    item.Check(check)
                if func.enabled:
                    gui.Bind(
                        wx.EVT_MENU,
                        menu_functions(func, node),
                        item,
                    )
                else:
                    item.Enable(False)
                if menu_context not in radio_check_not_needed:
                    radio_check_not_needed.append(menu_context)
            if not submenu and func.separate_after:
                last_was_separator = True
                menu.AppendSeparator()
        mc2 = menu.MenuItemCount
        if not last_was_separator and mc2 - mc1 > 0:
            menu.AppendSeparator()

    for func in elements.tree_operations_for_node(node):
        submenu_name = func.submenu
        submenu = None
        if submenu_name in submenus:
            submenu = submenus[submenu_name]
        else:
            if submenu_name is not None:
                submenu = wx.Menu()
                menu.AppendSubMenu(submenu, submenu_name, func.help)
                submenus[submenu_name] = submenu

        menu_context = submenu if submenu is not None else menu
        if func.separate_before:
            menu_context.AppendSeparator()
        if func.reference is not None:
            menu_context.AppendSubMenu(
                create_menu_for_node(gui, func.reference(node), elements),
                func.real_name,
            )
            continue
        if func.radio_state is not None:
            item = menu_context.Append(
                wx.ID_ANY, func.real_name, func.help, wx.ITEM_RADIO
            )
            check = func.radio_state
            item.Check(check)
            if check and menu_context not in radio_check_not_needed:
                radio_check_not_needed.append(menu_context)
            if func.enabled:
                gui.Bind(
                    wx.EVT_MENU,
                    menu_functions(func, node),
                    item,
                )
            else:
                item.Enable(False)
        else:
            if hasattr(func, "check_state") and func.check_state is not None:
                check = func.check_state
                kind = wx.ITEM_CHECK
            else:
                kind = wx.ITEM_NORMAL
                check = None
            item = menu_context.Append(wx.ID_ANY, func.real_name, func.help, kind)
            if check is not None:
                item.Check(check)
            if func.enabled:
                gui.Bind(
                    wx.EVT_MENU,
                    menu_functions(func, node),
                    item,
                )
            else:
                item.Enable(False)

            if menu_context not in radio_check_not_needed:
                radio_check_not_needed.append(menu_context)
        if not submenu and func.separate_after:
            menu.AppendSeparator()

    for submenu in submenus.values():
        if submenu not in radio_check_not_needed:
            item = submenu.Append(
                wx.ID_ANY,
                _("Other value..."),
                _("Value set using properties"),
                wx.ITEM_RADIO,
            )
            item.Check(True)
    return menu


def create_menu(gui, node, elements):
    """
    Create menu items. This is used for both the scene and the tree to create menu items.

    @param gui: Gui used to create menu items.
    @param node: The Node clicked on for the generated menu.
    @param elements: elements service for use with node creation
    @return:
    """
    if node is None:
        return
    # Is it a reference object?
    optional_node = None
    if hasattr(node, "node"):
        optional_node = node
        node = node.node

    menu = create_menu_for_node(gui, node, elements, optional_node)
    if menu.MenuItemCount != 0:
        gui.PopupMenu(menu)
        menu.Destroy()


class TextCtrl(wx.TextCtrl):
    # Just to add someof the more common things we need, i.e. smaller default size...
    #
    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        value="",
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=0,
        validator=wx.DefaultValidator,
        name="",
        check="",
        limited=False,
    ):
        super().__init__(
            parent,
            id=id,
            value=value,
            pos=pos,
            size=size,
            style=style,
            validator=validator,
            name=name,
        )
        self.SetMinSize(wx.Size(35, -1))
        if limited:
            self.SetMaxSize(wx.Size(100, -1))
        self._check = check
        self.lower_limit = None
        self.upper_limit = None
        self.lower_limit_err = None
        self.upper_limit_err = None
        self.lower_limit_warn = None
        self.upper_limit_warn = None
        self._default_color_background = None
        self._error_color_background = wx.RED
        self._warn_color_background = wx.YELLOW
        self._modify_color_background = None

        self._default_color_foreground = None
        self._error_color_foreground = None
        self._warn_color_foreground = wx.BLACK
        self._modify_color_foreground = None
        self._warn_status = "modified"

        if self._check is not None and self._check != "":
            self.Bind(wx.EVT_TEXT, self.on_check)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_leave)

    def set_error_level(self, err_min, err_max):
        self.lower_limit_err = err_min
        self.upper_limit_err = err_max

    def set_warn_level(self, warn_min, warn_max):
        self.lower_limit_warn = warn_min
        self.upper_limit_warn = warn_max

    def set_range(self, range_min, range_max):
        self.lower_limit = range_min
        self.upper_limit = range_max

    def on_leave(self, event):
        # Needs to be passed on
        event.Skip()
        self.SelectNone()
        # We assume it's been dealt with, so we recolor...
        self.SetModified(False)
        self.warn_status = self._warn_status

    def on_enter(self, event):
        # Let others deal with it after me
        event.Skip()
        # We assume it's been dealt with, so we recolor...
        self.SetModified(False)
        self.warn_status = self._warn_status

    @property
    def warn_status(self):
        return self._warn_status

    @warn_status.setter
    def warn_status(self, value):
        self._warn_status = value
        background = self._default_color_background
        foreground = self._default_color_foreground
        if value == "modified":
            # Is it modified?
            if self.IsModified():
                background = self._modify_color_background
                foreground = self._modify_color_foreground
        elif value == "warning":
            background = self._warn_color_background
            foreground = self._warn_color_foreground
        elif value == "error":
            background = self._error_color_background
            foreground = self._error_color_foreground
        self.SetBackgroundColour(background)
        self.SetForegroundColour(foreground)
        self.Refresh()

    def on_check(self, event):
        event.Skip()
        status = "modified"
        try:
            txt = self.GetValue()
            value = None
            if self._check == "float":
                value = float(txt)
            elif self._check == "percent":
                if txt.endswith("%"):
                    value = float(txt[:-1]) / 100.0
                else:
                    value = float(txt)
            elif self._check == "int":
                value = int(txt)
            elif self._check == "empty":
                if len(txt) == 0:
                    status = "error"
            elif self._check == "length":
                value = Length(txt)
            elif self._check == "angle":
                value = Angle(txt)
            # we passed so far, thus the values are syntactically correct
            # Now check for content compliance
            if value is not None:
                if self.lower_limit is not None and value < self.lower_limit:
                    value = self.lower_limit
                    self.SetValue(str(value))
                    status = "default"
                if self.upper_limit is not None and value > self.upper_limit:
                    value = self.upper_limit
                    self.SetValue(str(value))
                    status = "default"
                if self.lower_limit_warn is not None and value < self.lower_limit_warn:
                    status = "warning"
                if self.upper_limit_warn is not None and value > self.upper_limit_warn:
                    status = "warning"
                if self.lower_limit_err is not None and value < self.lower_limit_err:
                    status = "error"
                if self.upper_limit_err is not None and value > self.upper_limit_err:
                    status = "error"
        except ValueError:
            status = "error"
        self.warn_status = status


class CheckBox(wx.CheckBox):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self._tool_tip = None
        super().__init__(*args, **kwargs)
        if platform.system() == "Linux":
            def on_mouse_over_check(ctrl):
                def mouse(event=None):
                    ctrl.SetToolTip(self._tool_tip)

                return mouse
            self.Bind(wx.EVT_MOTION, on_mouse_over_check(super()))

    def SetToolTip(self, tooltip):
        self._tool_tip = tooltip
        super().SetToolTip(self._tool_tip)


class ScrolledPanel(SP):
    """
    We sometimes delete things fast enough that they call _SetupAfter when dead and crash.
    """

    def _SetupAfter(self, scrollToTop):
        try:
            self.SetVirtualSize(self.GetBestVirtualSize())
            if scrollToTop:
                self.Scroll(0, 0)
        except RuntimeError:
            pass


WX_METAKEYS = [
    wx.WXK_START,
    wx.WXK_WINDOWS_LEFT,
    wx.WXK_WINDOWS_RIGHT,
]

WX_MODIFIERS = {
    wx.WXK_CONTROL: "ctrl",
    wx.WXK_RAW_CONTROL: "macctl",
    wx.WXK_ALT: "alt",
    wx.WXK_SHIFT: "shift",
    wx.WXK_START: "start",
    wx.WXK_WINDOWS_LEFT: "win-left",
    wx.WXK_WINDOWS_RIGHT: "win-right",
}

WX_SPECIALKEYS = {
    wx.WXK_F1: "f1",
    wx.WXK_F2: "f2",
    wx.WXK_F3: "f3",
    wx.WXK_F4: "f4",
    wx.WXK_F5: "f5",
    wx.WXK_F6: "f6",
    wx.WXK_F7: "f7",
    wx.WXK_F8: "f8",
    wx.WXK_F9: "f9",
    wx.WXK_F10: "f10",
    wx.WXK_F11: "f11",
    wx.WXK_F12: "f12",
    wx.WXK_F13: "f13",
    wx.WXK_F14: "f14",
    wx.WXK_F15: "f15",
    wx.WXK_F16: "f16",
    wx.WXK_F17: "f17",
    wx.WXK_F18: "f18",
    wx.WXK_F19: "f19",
    wx.WXK_F20: "f20",
    wx.WXK_F21: "f21",
    wx.WXK_F22: "f22",
    wx.WXK_F23: "f23",
    wx.WXK_F24: "f24",
    wx.WXK_ADD: "+",
    wx.WXK_END: "end",
    wx.WXK_NUMPAD0: "numpad0",
    wx.WXK_NUMPAD1: "numpad1",
    wx.WXK_NUMPAD2: "numpad2",
    wx.WXK_NUMPAD3: "numpad3",
    wx.WXK_NUMPAD4: "numpad4",
    wx.WXK_NUMPAD5: "numpad5",
    wx.WXK_NUMPAD6: "numpad6",
    wx.WXK_NUMPAD7: "numpad7",
    wx.WXK_NUMPAD8: "numpad8",
    wx.WXK_NUMPAD9: "numpad9",
    wx.WXK_NUMPAD_ADD: "numpad_add",
    wx.WXK_NUMPAD_SUBTRACT: "numpad_subtract",
    wx.WXK_NUMPAD_MULTIPLY: "numpad_multiply",
    wx.WXK_NUMPAD_DIVIDE: "numpad_divide",
    wx.WXK_NUMPAD_DECIMAL: "numpad.",
    wx.WXK_NUMPAD_ENTER: "numpad_enter",
    wx.WXK_NUMPAD_RIGHT: "numpad_right",
    wx.WXK_NUMPAD_LEFT: "numpad_left",
    wx.WXK_NUMPAD_UP: "numpad_up",
    wx.WXK_NUMPAD_DOWN: "numpad_down",
    wx.WXK_NUMPAD_DELETE: "numpad_delete",
    wx.WXK_NUMPAD_INSERT: "numpad_insert",
    wx.WXK_NUMPAD_PAGEUP: "numpad_pgup",
    wx.WXK_NUMPAD_PAGEDOWN: "numpad_pgdn",
    wx.WXK_NUMPAD_HOME: "numpad_home",
    wx.WXK_NUMPAD_END: "numpad_end",
    wx.WXK_NUMLOCK: "num_lock",
    wx.WXK_SCROLL: "scroll_lock",
    wx.WXK_CAPITAL: "caps_lock",
    wx.WXK_HOME: "home",
    wx.WXK_DOWN: "down",
    wx.WXK_UP: "up",
    wx.WXK_RIGHT: "right",
    wx.WXK_LEFT: "left",
    wx.WXK_ESCAPE: "escape",
    wx.WXK_BACK: "back",
    wx.WXK_PAUSE: "pause",
    wx.WXK_PAGEDOWN: "pagedown",
    wx.WXK_PAGEUP: "pageup",
    wx.WXK_PRINT: "print",
    wx.WXK_RETURN: "return",
    wx.WXK_SPACE: "space",
    wx.WXK_TAB: "tab",
    wx.WXK_DELETE: "delete",
    wx.WXK_INSERT: "insert",
    wx.WXK_SPECIAL1: "special1",
    wx.WXK_SPECIAL2: "special2",
    wx.WXK_SPECIAL3: "special3",
    wx.WXK_SPECIAL4: "special4",
    wx.WXK_SPECIAL5: "special5",
    wx.WXK_SPECIAL6: "special6",
    wx.WXK_SPECIAL7: "special7",
    wx.WXK_SPECIAL8: "special8",
    wx.WXK_SPECIAL9: "special9",
    wx.WXK_SPECIAL10: "special10",
    wx.WXK_SPECIAL11: "special11",
    wx.WXK_SPECIAL12: "special12",
    wx.WXK_SPECIAL13: "special13",
    wx.WXK_SPECIAL14: "special14",
    wx.WXK_SPECIAL15: "special15",
    wx.WXK_SPECIAL16: "special16",
    wx.WXK_SPECIAL17: "special17",
    wx.WXK_SPECIAL18: "special18",
    wx.WXK_SPECIAL19: "special19",
    wx.WXK_SPECIAL20: "special20",
    wx.WXK_CLEAR: "clear",
    wx.WXK_WINDOWS_MENU: "menu",
}

def is_navigation_key(keyvalue):
    if keyvalue is None:
        return False
    if "right" in keyvalue:
        return True
    if "left" in keyvalue:
        return True
    if "up" in keyvalue and "pgup" not in keyvalue and "pageup" not in keyvalue:
        return True
    if "down" in keyvalue and "pagedown" not in keyvalue:
        return True
    if "tab" in keyvalue:
        return True
    if "return" in keyvalue:
        return True
    return False

def get_key_name(event, return_modifier=False):
    keyvalue = ""
    # https://wxpython.org/Phoenix/docs/html/wx.KeyEvent.html
    key = event.GetUnicodeKey()
    if key == wx.WXK_NONE:
        key = event.GetKeyCode()
    if event.RawControlDown() and not event.ControlDown():
        keyvalue += "macctl+"  # Deliberately not macctrl+
    elif event.ControlDown():
        keyvalue += "ctrl+"
    if event.AltDown() or key == wx.WXK_ALT:
        keyvalue += "alt+"
    if event.ShiftDown():
        keyvalue += "shift+"
    if event.MetaDown() or key in WX_METAKEYS:
        keyvalue += "meta+"
    # if return_modifier and keyvalue: print("key", key, keyvalue)
    if key in WX_MODIFIERS:
        return keyvalue if return_modifier else None
    if key in WX_SPECIALKEYS:
        keyvalue += WX_SPECIALKEYS[key]
    else:
        keyvalue += chr(key)
    # print("key", key, keyvalue)
    return keyvalue.lower()


def disable_window(window):
    for m in window.Children:
        if hasattr(m, "Disable"):
            m.Disable()
        if hasattr(m, "Children"):
            disable_window(m)


def set_ctrl_value(ctrl, value):
    # Let's try to save the caret position
    cursor = ctrl.GetLastPosition()
    if ctrl.GetValue() != value:
        ctrl.SetValue(value)
        ctrl.SetInsertionPoint(min(len(value), cursor))
