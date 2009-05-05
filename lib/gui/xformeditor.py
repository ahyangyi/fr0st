import wx, os
from wx import gizmos
from itertools import chain
from collections import defaultdict

from decorators import Bind,BindEvents
from lib.fr0stlib import polar, rect
from lib import pyflam3


def LoadIcon(name):
    img = wx.Image(os.path.join('lib','gui','icons','xformtab',"%s.png" %name),
                                type=wx.BITMAP_TYPE_PNG)
    img.Rescale(16, 16)
    return wx.BitmapFromImage(img)


class XformTabs(wx.Notebook):


    def __init__(self, parent):
        self.parent = parent
        wx.Notebook.__init__(self, parent, -1, size=(21,21), style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
                             )

        self.Xform = XformPanel(self)
        self.AddPage(self.Xform, "Xform")

        self.Vars = VarPanel(self)
        self.AddPage(self.Vars, "Vars")

        win = wx.Panel(self, -1)
        self.AddPage(win, "Color")

        win = wx.Panel(self, -1)
        self.AddPage(win, "Xaos")

        self.Selector = wx.Choice(self.parent, -1)
        self.Selector.Bind(wx.EVT_CHOICE, self.OnChoice)


    def UpdateView(self):
        for i in self.Xform, self.Vars:
            i.UpdateView()
        choices = map(repr, self.parent.flame.xform)
        final = self.parent.flame.final
        if final:
            choices.append(repr(final))
        self.Selector.Items = choices
        index = self.parent.ActiveXform.index
        self.Selector.Selection = len(choices)-1 if index is None else index


    def OnChoice(self, e):
        index = e.GetInt()
        xforms = self.parent.flame.xform
        if index >= len(xforms):
            self.parent.ActiveXform = self.parent.flame.final
        else:
            self.parent.ActiveXform = xforms[index]

        self.parent.canvas.ShowFlame(rezoom=False)
        self.UpdateView()



class XformPanel(wx.Panel):
    _rotate = 15
    _translate = 0.1
    _scale = 1.25

    choices = {"rotate": map(str, (5, 15, 30, 45, 60, 90, 120, 180)),
               "translate": map(str,(1.0, 0.5, 0.25, 0.1, 0.05, 0.025, 0.001)),
               "scale": map(str, (1.1, 1.25, 1.5, 1.75, 2.0))}

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        # The view tells us what attributes need to be displayed
        self._view = [False, "triangle"]
        self.parent = parent.parent

        # Add the number fields
        map(lambda x: setattr(self,x,NumberTextCtrl(self)), "adbecf")
        btn = (wx.Button(self,-1,i,name=i,style=wx.BU_EXACTFIT) for i in "xyo")

        fgs = wx.FlexGridSizer(3,3,1,1)
        itr = (getattr(self, i) for i in "adbecf")
        fgs.AddMany(chain(*zip(btn, itr, itr)))


        # Add the view buttons
        r1 = wx.RadioButton(self, -1, "triangle", style = wx.RB_GROUP )
        r2 = wx.RadioButton(self, -1, "xform" )
        r3 = wx.RadioButton(self, -1, "polar" )
        postflag = wx.CheckBox(self,-1,"post")
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddMany((r1,r2,r3,postflag))

        # Put the view buttons to the right of the number fields
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddMany((fgs, vsizer))

        # Add the reset xform button
        reset = wx.Button(self, -1, "reset xform", name="Reset",
                          style=wx.BU_EXACTFIT)

        # Add the rotation, translation and scale buttons
        self.rotate = wx.ComboBox(self, -1, "15", name="rotate", size=(80,28),
                                  choices=self.choices["rotate"])
       
        self.translate = wx.ComboBox(self, -1, "0.1", name="translate", size=(80,28),
                                  choices=self.choices["translate"])
         
        self.scale = wx.ComboBox(self, -1, "1.25", name="scale", size=(80,28),
                                  choices=self.choices["scale"])

        btn = [wx.BitmapButton(self, -1, LoadIcon(i), name=i.replace("-",""))
               for i in ('90-Left', 'Rotate-Left', 'Rotate-Right', '90-Right',
                         'Move-Up', 'Move-Down', 'Move-Left', 'Move-Right',
                         'Shrink', 'Grow')]
        
        btn.insert(2, self.rotate)
        btn.insert(7, self.translate)
        btn.insert(10, (0,0))
        btn.insert(12, self.scale)
        
        fgs2 = wx.FlexGridSizer(4, 5, 1, 1)
        fgs2.AddMany(btn)        
        
        # Finally, put everything together
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddMany((hsizer, reset, fgs2))
        self.SetSizer(sizer)
        self.Layout()
        

    @Bind(wx.EVT_RADIOBUTTON)
    def OnRadioSelected(self,e):
        self._view[1] = e.GetEventObject().GetLabel()
        self.UpdateView()


    @Bind(wx.EVT_CHECKBOX)
    def OnPostCheckbox(self,e):
        self._view[0] = e.IsChecked()
        self.UpdateView()


    @Bind(wx.EVT_TEXT)
    def OnComboChar(self, e):
        combobox = e.GetEventObject()
        if combobox not in (self.rotate, self.translate, self.scale):
            # BUG: It's some other object raising this event (WHY?)
            return
        val = "".join(char for char in e.GetString() if char in "0123456789.-")
        combobox.SetValue(val)
        

    @Bind(wx.EVT_BUTTON)
    def OnButton(self, e):
        xform, view = self.GetActive()
        name = e.GetEventObject().GetName()
        for i in "rotate", "translate", "scale":
            combobox = getattr(self, i)
            try:
                setattr(self, "_%s" %i, float(combobox.GetValue()))
            except:
                combobox.SetValue(str(getattr(self, "_%s" %i)))
                
        getattr(self, "Func%s" %name)(xform)
        self.parent.TreePanel.TempSave()


    def Funcx(self, xform):
        xform.a, xform.d = 1,0

    def Funcy(self, xform):
        xform.b, xform.e = 0,1

    def Funco(self, xform):
        xform.c, xform.f = 0,0

    def FuncReset(self, xform):
        xform.coefs = 1,0,0,1,0,0

    def Func90Left(self, xform):
        xform.rotate(90)

    def FuncRotateLeft(self, xform):
        xform.rotate(self._rotate)

    def FuncRotateRight(self, xform):
        xform.rotate(-self._rotate)

    def Func90Right(self, xform):
        xform.rotate(-90)

    def FuncMoveUp(self, xform):
        xform.move_position(0, self._translate)

    def FuncMoveDown(self, xform):
        xform.move_position(0, -self._translate)

    def FuncMoveLeft(self, xform):
        xform.move_position(-self._translate, 0)

    def FuncMoveRight(self, xform):
        xform.move_position(self._translate, 0)

    def FuncShrink(self, xform):
        xform.scale(1.0/self._scale)

    def FuncGrow(self, xform):
        xform.scale(self._scale)


    def GetActive(self):
        post, view = self._view
        xform = self.parent.ActiveXform
        if post:
            xform = xform.post
        return xform, view


    def UpdateView(self):
        xform, view = self.GetActive()
            
        if view == "triangle":
            self.coefs = chain(*xform.points)
        elif view == "xform":
            self.coefs = xform.coefs
        elif view == "polar":
            self.coefs = chain(*map(polar, zip(*[iter(xform.coefs)]*2)))


    def UpdateXform(self,e=None):
        xform, view = self.GetActive()

        if view == "triangle":
            xform.points = zip(*[iter(self.coefs)]*2)
        elif view == "xform":
            xform.coefs = self.coefs
        elif view == "polar":
            xform.coefs = chain(*map(rect, [iter(self.coefs)]*2))

        self.parent.TreePanel.TempSave()
                                          

    def _get_coefs(self):
        return (getattr(self,i).GetFloat() for i in "adbecf")

    def _set_coefs(self,v):
        map(lambda x,y: getattr(self,x).SetFloat(y),"adbecf",v)

    coefs = property(_get_coefs, _set_coefs)

#------------------------------------------------------------------------------

class VarPanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent.parent

        self.tree = gizmos.TreeListCtrl(self, -1, style =
                                          wx.TR_DEFAULT_STYLE
                                        | wx.TR_ROW_LINES
                                        | wx.TR_COLUMN_LINES
                                        | wx.TR_NO_LINES
                                        | wx.TR_HIDE_ROOT
                                        | wx.TR_FULL_ROW_HIGHLIGHT
                                   )

        self.tree.AddColumn("Var")
        self.tree.AddColumn("Value")

        self.tree.SetMainColumn(0)
        self.tree.SetColumnWidth(0, 160)
        self.tree.SetColumnWidth(1, 60)
        self.tree.SetColumnEditable(1,True)

        self.root = self.tree.AddRoot("The Root Item")

        for i in pyflam3.variation_list:
            child = self.tree.AppendItem(self.root, i)

            for j in pyflam3.variables[i]:
                item = self.tree.AppendItem(child,  j)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree,1,wx.EXPAND)
        self.SetSizer(sizer)

        self.tree.GetMainWindow().Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        self.parent.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.HasChanged = False


    def itervars(self, item=None):
        if not item:
            item = self.root
        child,cookie = self.tree.GetFirstChild(item)  
        while child.IsOk():
            name = self.tree.GetItemText(child)
            yield (child, name)
            for i,_ in self.itervars(child):
                yield (i, "%s_%s" % (name, self.tree.GetItemText(i)))
            child,cookie = self.tree.GetNextChild(item,cookie)
            

    def UpdateView(self):
        xform = self.parent.ActiveXform
        for i,name in self.itervars():
            self.tree.SetItemText(i, str(getattr(xform, name)), 1)


    def SetFlameAttribute(self, item, value):
        parent = self.tree.GetItemParent(item)
        if parent == self.root:
            # it's a variation
            name = self.tree.GetItemText(item, 0)
        else:
            # it's a variable
            name = "_".join(map(self.tree.GetItemText,(parent,item)))
        setattr(self.parent.ActiveXform,name,value)


    @Bind(wx.EVT_TREE_END_LABEL_EDIT)
    def OnEndEdit(self, e):
        item = e.GetItem()
        oldvalue = self.tree.GetItemText(item, 1)
        try:
            value = float(e.GetLabel() or "0.0")
            self.tree.SetItemText(item,str(value),1)
        except ValueError:
            e.Veto()
            return

        if value != oldvalue:
            self.SetFlameAttribute(item, value)
            self.parent.TreePanel.TempSave()

        e.Veto()


    # TODO: is it preferrable to have:
    #   -SEL_CHANGED:    immediate edit of values
    #   -ITEM_ACTIVATED: ability to search with letters.
    @Bind(wx.EVT_TREE_ITEM_ACTIVATED)
##    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self,e):
        item = e.GetItem()
        if item != self.root:
            self.tree.EditLabel(item,1)
        e.Veto()


    def OnWheel(self,e):
        if e.ControlDown():
            if e.AltDown():
                diff = 0.01
            else:
                diff = 0.1
        elif e.AltDown():
            diff = 0.001
        else:
            e.Skip()
            return

        self.SetFocus() # Makes sure OKeyUp gets called.
        
        item = self.tree.HitTest(e.GetPosition())[0]
        name = self.tree.GetItemText(item)
        val = self.tree.GetItemText(item, 1) or "0.0"
        
        val = float(val) + (diff if e.GetWheelRotation() > 0 else -diff)
        self.SetFlameAttribute(item, val)
        self.tree.SetItemText(item, str(val), 1)
        self.parent.image.RenderPreview()
        self.HasChanged = True
        

    def OnKeyUp(self, e):
        key = e.GetKeyCode()
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.HasChanged:
                self.parent.TreePanel.TempSave()
                self.HasChanged = False
            

class NumberTextCtrl(wx.TextCtrl):

    @BindEvents
    def __init__(self,parent):
        self.parent = parent
        # Size is set to ubuntu default (75,27), maybe make it 75x21 in win
        wx.TextCtrl.__init__(self,parent,-1, size=(75,27))
        self.SetValue("0.0")
        self._value = 0.0

    def GetFloat(self):
        return float(self.GetValue() or "0")
##
    def SetFloat(self,v):
        v = float(v) # Make sure pure ints don't make trouble
        self.SetValue(str(v))
        self._value = v


    @Bind(wx.EVT_CHAR)
    def OnChar(self, event):
        key = event.GetKeyCode()

        if key in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            self.OnKillFocus(None)
            
        elif key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()

        elif chr(key) in "0123456789.-":
            event.Skip()  

        else:
            # not calling Skip() eats the event
            pass #wx.Bell()


    @Bind(wx.EVT_KILL_FOCUS)
    def OnKillFocus(self,event):
        # This comparison is done with strings because the floats don't
        # always compare equal (!)
        if str(self._value) != self.GetValue():
            try:
                self._value = self.GetFloat()
                self.parent.UpdateXform()
            except ValueError:
                self.SetFloat(self._value)

