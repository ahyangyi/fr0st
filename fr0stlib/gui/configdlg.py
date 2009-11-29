##############################################################################
#  Fractal Fr0st - fr0st
#  https://launchpad.net/fr0st
#
#  Copyright (C) 2009 by Vitor Bosshard <algorias@gmail.com>
#
#  Fractal Fr0st is free software; you can redistribute
#  it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Library General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this library; see the file COPYING.LIB.  If not, write to
#  the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#  Boston, MA 02111-1307, USA.
##############################################################################
import wx
from operator import setitem


from copy import deepcopy
from fr0stlib.decorators import *
from fr0stlib.gui.config import config, update_dict
from fr0stlib.gui.utils import NumberTextCtrl, Box
from fr0stlib.pyflam3.cuda import is_cuda_capable


class ConfigDialog(wx.Dialog):

    @BindEvents
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title='Preferences')

        # save a copy of config to work with
        # allows us to implement cancel
        self.local_config = deepcopy(config)
        self.controls = {}

        notebook = wx.Notebook(self, style=wx.BK_DEFAULT)
        notebook.AddPage(self.CreatePreviewSettings(notebook),
                         'Preview Quality', select=True)
        notebook.AddPage(RenderPanel(notebook), 'Renderer')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 0, wx.ALL, 5)

        btnsizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)

        if btnsizer:
            sizer.Add(btnsizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        self.SetSizerAndFit(sizer)

        self.controls['Var-Preview-Settings->range'].SetFocus()
        

    @Bind(wx.EVT_BUTTON, id=wx.ID_OK)
    @Bind(wx.EVT_BUTTON, id=wx.ID_CANCEL)
    def OnOK(self, evt):
        self.EndModal(evt.GetId())

    def CreatePreviewSettings(self, parent):
        panel = wx.Panel(parent)
        gbs = wx.GridBagSizer(5, 5)
        gbs.Add(self.CreateVariationPreviewSettings(panel), (0, 0), flag=wx.EXPAND)
        gbs.Add(self.CreateSmallPreviewSettings(panel), (1, 0), (1, 1), flag=wx.EXPAND)
        gbs.Add(self.CreateLargePreviewSettings(panel), (0, 1), (2, 1))
        panel.SetSizerAndFit(gbs)
        return panel
        

    def number_text(self, parent, sizer, row, label, config_section, config_key, min, max, is_int=False):
        ntc = NumberTextCtrl(parent, min, max)
        
        if is_int:
            ntc.MakeIntOnly()

        section = self.local_config[config_section]
        self.controls[config_section + '->' + config_key] = ntc

        ntc.SetFloat(section[config_key])
        ntc.callback = lambda tempsave=False: setitem(section, config_key, ntc.GetFloat())

        sizer.Add(wx.StaticText(parent, label=label), (row, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(ntc, (row, 1))
        
    def CreateVariationPreviewSettings(self, parent):
        gbs = wx.GridBagSizer(5, 5)
        gbs.AddGrowableCol(0)

        self.number_text(parent, gbs, 0, 'Scale', 
                'Var-Preview-Settings', 'range', 0.1, 5)
        
        self.number_text(parent, gbs, 1, 'Quality', 
                'Var-Preview-Settings', 'numvals', 10, 40, is_int=True)

        self.number_text(parent, gbs, 2, 'Depth',
                'Var-Preview-Settings', 'depth', 1, 5, is_int=True) 

        return Box(parent, 'Variation Preview', (gbs, 0, wx.EXPAND))

    def CreateSmallPreviewSettings(self, parent):
        gbs = wx.GridBagSizer(5, 5)
        gbs.AddGrowableCol(0)

        self.number_text(parent, gbs, 0, 'Quality', 
                'Preview-Settings', 'quality', 1, 20, is_int=True)

        self.number_text(parent, gbs, 1, 'Density Estimator', 
                'Preview-Settings', 'estimator', 0, 20, is_int=True)

        self.number_text(parent, gbs, 2, 'Filter Radius', 
                'Preview-Settings', 'filter_radius', 0, 10)

        return Box(parent, 'Preview', (gbs, 0, wx.EXPAND))

    def CreateLargePreviewSettings(self, parent):
        gbs = wx.GridBagSizer(5, 5)
        gbs.AddGrowableCol(0)

        self.number_text(parent, gbs, 0, 'Quality', 
                'Large-Preview-Settings', 'quality', 1, 1000, is_int=True)

        self.number_text(parent, gbs, 1, 'Density Estimator', 
                'Large-Preview-Settings', 'estimator', 0, 20, is_int=True)

        self.number_text(parent, gbs, 2, 'Filter Radius', 
                'Large-Preview-Settings', 'filter_radius', 0, 10)

        self.number_text(parent, gbs, 3, 'Oversample', 
                'Large-Preview-Settings', 'spatial_oversample', 0, 5, is_int=True)

        return Box(parent, 'Large Preview', (gbs, 0, wx.EXPAND))

    def CommitChanges(self):
        update_dict(config, self.local_config)
        # Immediately update canvas to see eventual changes in var preview.
        self.Parent.canvas.ShowFlame(rezoom=False)




class RenderPanel(wx.Panel):
    @BindEvents
    def __init__(self, parent):
        self.parent = parent.Parent
        wx.Panel.__init__(self, parent, -1)

        if is_cuda_capable():
            choices = ["flam3", "flam4"]
        else:
            choices = ["flam3"]
        
        self.rb = wx.RadioBox(self, -1, label="Renderer", choices=choices,
                              style=wx.RA_VERTICAL)
        self.rb.SetStringSelection(self.parent.local_config["renderer"])

        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(self.rb)
        self.SetSizerAndFit(szr)
        

    @Bind(wx.EVT_RADIOBOX)
    def OnRadio(self, e):
        self.parent.local_config["renderer"] = self.rb.GetStringSelection()
        

