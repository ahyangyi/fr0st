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
import wx, os

from fr0stlib.pyflam3 import Genome
from fr0stlib import Flame, needs_conversion


types = {".bmp": wx.BITMAP_TYPE_BMP,
         ".png": wx.BITMAP_TYPE_PNG,
         ".jpg": wx.BITMAP_TYPE_JPEG}


def save_image(path, img):
    if isinstance(img, wx.Bitmap):
        img = wx.ImageFromBitmap(img)
    ty = types[os.path.splitext(path)[1]]
    dirname = os.path.abspath(os.path.dirname(path))
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    img.SaveFile(path, ty)



def flam3_render(flame, size, quality, **kwds):
    """Passes render requests on to flam3."""
    if isinstance(flame, basestring):
        if needs_conversion(flame):
            genome = Genome.from_string(Flame(flame).to_string())[0]
        else:
            genome = Genome.from_string(flame)[0]
    else:
        genome = Genome.from_string(flame.to_string())[0]

    width,height = size

    try:
        genome.pixels_per_unit /= genome.width/float(width) # Adjusts scale
    except ZeroDivisionError:
        raise ZeroDivisionError("Size passed to render function is 0.")
    
    genome.width = width
    genome.height = height
    genome.sample_density = quality
    output_buffer, stats = genome.render(**kwds)
    return output_buffer


def flam4_render(flame, size, quality, **kwds):
    """Passes requests on to flam4. Works on windows only for now."""
    from fr0stlib.pyflam3 import _flam4
    flame = flame if type(flame) is Flame else Flame(flame)
    flam4Flame = _flam4.loadFlam4(flame)
    output_buffer = _flam4.renderFlam4(flam4Flame, size, quality, **kwds)
    return output_buffer


render_funcs = {'flam3': flam3_render,
                'flam4': flam4_render}
