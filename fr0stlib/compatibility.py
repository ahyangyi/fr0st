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
from math import log10




def percent2log(prc):
    return 10.0 ** (-log10(1.0/prc)/log10(2.0))

def log2percent(logval):
    return 2.0 ** log10(logval) if logval else 0.0


def compatibilize(flame, version):
    if getattr(flame, "version", "").startswith("fr0st"):
        return
    
    # Assume the flame is compatible with apo and flam3 < 2.8
    apo2fr0st(flame)

    flame.version = version
    

def apo2fr0st(flame):
    """Convert all attributes to be compatible with flam3 2.8."""
    # zoom is deprecated, so scale is adjusted by the zoom value
    if hasattr(flame, "zoom"):
        flame.scale *= 2**flame.zoom
        del flame.zoom
        
    # Symmetry is deprecated, so we factor it into the equivalent attrs.
    for x in flame.iter_xforms():
        x.color_speed = x.__dict__.get("color_speed", (1 - x.symmetry) / 2.0)
        x.animate = x.__dict__.get("animate", float(x.symmetry <= 0))
        x.symmetry = 0.0
        
    # plotmode was never a good idea
    for x in flame.xform:
        if type(x.plotmode) is str and x.plotmode.lower() == "off":
            x.opacity = 0.0
            del x.plotmode
    
    # neither was soloxform
    if hasattr(flame, "soloxform"):
        for x in flame.xform:
            x.opacity = float(x.index == flame.soloxform)
        del flame.soloxform
         
    # chaos is converted from linear scale to log scale.
    from fr0stlib import Chaos
    for x in flame.iter_xforms():
        x.chaos = Chaos(x, map(log2percent, x.chaos))


