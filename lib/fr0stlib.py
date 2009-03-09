#Copyright (c) 2008 Vitor Bosshard
#This program licensed under the GPL. See license.txt for details.
#
#Tested under:
#Python 2.6.1
#Pygame 1.8.1.win32-py2.5
#-----------------------------------------------------------------

import os, sys, re, copy, itertools
from math import *
    

class ParsingError(Exception):
    pass



class Flame(object):
    re_flame  = re.compile(r'<flame .*?</flame>',re.DOTALL)
    re_header = re.compile(r'<flame .*?>')
    re_xform  = re.compile(r'<[a-zA-Z]*xform .*?/>')
    re_attr   = re.compile(r'[^ ]*?=".*?(?=")') # Works for xforms and header  
##    re_grad   = re.compile(r'[0-9A-F]{6}(?=[0-9A-F]*.?$)',re.MULTILINE)

    _default = ["_scale","final","gradient","xform","pixels"]

    
    def __init__(self,file="",string="",name=""):
        """A new flame object can be created by passing it a filename or
        a string. If name is not specified, the first flame will be taken."""

        self.gradient = []
        self.xform = []

        if not string and file:
            path = os.path.join(sys.path[0],"parameters",file)
            lst = Flame.load_file(path)
            if not name:
                string = lst[0]
            else:
                for flame in Flame.load_file(path):
                    if 'name="%s"' %name in flame:
                        string = flame ; break
                   
        if not string:
            raise NameError, 'Flame "%s" not found' %name
        self.from_string(string)

    @classmethod
    def load_file(cls,filename):
        """Retrieves all flame data from a flame file and turns it
        into strings."""
        f = open(filename,"r")
        flamestrings = cls.re_flame.findall(f.read())
        f.close()
        return flamestrings

            
    def from_string(self,string):
        counter = 0

        # Set required attributes that might be missing in the file.  
        self.size = [800,600]
        self.zoom = 0.0
        self.center = [0.0,0.0]
        self.rotate = 0.0
        self.background = [0.0,0.0,0.0]
        self.final = None
        self.scale = 0.0

        # Record the header data
        for attr in self.re_attr.findall(self.re_header.search(string).group()):
            name, val = attr.split('="')
                
            # Convert value to the appropriate type
            try:
                if " " in val: val = map(float,val.split())
                else:          val = float(val)
            except ValueError:
                pass   # Keep as string
            
            setattr(self,name,val)

        # Scale needs to be converted to Apo notation. This is reversed in
        # the to_string method
        self.scale = self.scale * 100 / self.size[0]
            
        # Create the gradient
        self.gradient = Palette(string)
                
        # Create the Xform objects
        for xform in self.re_xform.findall(string):
            parameters = []
            for string in self.re_attr.findall(xform):
                name, val = string.split('="')
                try:
                    if " " in val: param = name, map(float,val.split())
                    else:          param = name, float(val)
                except ValueError:
                    param = name, val
                    
                parameters.append(param)

            x = Xform(self,*parameters)              

            # Assign the xform to the correct location, 
            if x.weight:
                self.xform.append(x)
            elif not self.final:
                self.final = x
            else:
                raise ParsingError("More than one final xform found")

    def to_string(self,include_details=True):
        """Extracts parameters from a Flame object and converts them into string format."""

        lst =  ['<flame ']
        # Write the flame header
        if include_details:
            for name,val in self.iter_attributes():
                _type = type(val)
                if   _type is list or _type is tuple:
                    # Remember to convert round numbers to integer.
                    param = name," ".join(str(i if i%1 else int(i)) for i in val)
                elif _type is str:
                    param = name, val
                elif name == "scale":
                    param = name, val * self.size[0] / 100
                else:
                    param = name, val if val%1 else int(val)
                lst.append('%s="%s" ' %param)
            lst.append('>')
        else:
            lst.append('name="fr0st" >')

        # Make each xform       
        xformlist = self.xform[:]
        if self.final:
            xformlist.append(self.final)
        for xform in xformlist:
            lst.append('\n   <%sxform '%("final" if xform is self.final else ""))
            for name,val in xform.iter_attributes():
                lst.append('%s="%s" ' %(name,val))

            lst.append('coefs="%s %s %s %s %s %s" ' % xform.get_screen_coefs())

            # Write the post xform only if it isn't neutral.
            post = xform.post.get_screen_coefs()
            if post != (1,0,0,1,0,0):
                lst.append('post="%s %s %s %s %s %s" ' % post)

            # Write the chaos values.
            xaos = xform.chaos.get_list()
            if xaos:
                lst.append('chaos="%s" />' %" ".join(map(str,xaos)))
            else:
                lst.append('/>')
        
        # Make the gradient
        if include_details:
            lst.append(self.gradient.to_string())

        lst.append('</flame>\n')

        return "".join(lst)


    def create_final(self):
        if self.final: return
        self.final = Xform(self,
                           ("coefs",[1,0,0,1,0,0]),
                           ("linear",1),
                           ("color",0))

    def add_xform(self):
        self.xform.append(Xform(self,
                                ("coefs",[1,0,0,1,0,0]),
                                ("linear",1),
                                ("color",0)))

    def clear(self):
        self.xform = []
        self.final = None
        
    def _get_angle(self):
        return radians(self.rotate)

    def _set_angle(self,v):
        self.rotate = degrees(v)

    angle = property(_get_angle,_set_angle)

    def _get_attributes(self):
        return [i for i in self.__dict__ if i not in self._default]

    attributes = property(_get_attributes)

    def iter_attributes(self):
        return ((k,v) for (k,v) in self.__dict__.iteritems()
                if k not in self._default)

    def _get_width(self):
        return self.size[0]

    def _set_width(self,v):
        self.size[0] = v

    width = property(_get_width,_set_width)

    def _get_height(self):
        return self.size[0]

    def _set_height(self,v):
        self.size[0] = v

    height = property(_get_height,_set_height)



class Palette(list):
    re_grad   = re.compile(r'[0-9A-F]{6}(?=[0-9A-F]*.?$)',re.MULTILINE)
    formatstr = ('\n   <palette count="256" format="RGB">' +
                 32 * ('\n      ' + 24 * '%02X') +
                 '\n   </palette>\n')
    
    def __init__(self,string):
        for i in self.re_grad.findall(string):
            self.append((int(i[0:2],16),
                         int(i[2:4],16),
                         int(i[4:6],16)))
        if len(self) != 256:
            raise ParsingError("Palette data unreadable")

    def to_string(self):  
        return self.formatstr % tuple(itertools.chain(*self))



class Xform(object):
    """Container for transform parameters."""

    _default = ["_parent","a","b","c","d","e","f","_chaos","_post"]
    
    def __repr__(self):
        if self is self._parent.final:
            return "<finalxform>"
        else:
            return "<xform %d>" % self._parent.xform.index(self)
      
    def __getattr__(self,v):
        "Returns a default value for non-existing attributes"
        try:
            return object.__getattribute__(self,v)
        except AttributeError:
            if v.startswith('__'):
                raise
            return 0.0

    def __setattr__(self,name,v):
        """Deletes all attributes that are set to the default value"""
        if v == 0 and name != "color":
            try:
                delattr(self,name)
            except AttributeError:
                pass
        else:
            object.__setattr__(self,name,v)

    def __init__(self,parent,*args):
        self._parent = parent
        for name,val in args:
            if name == 'chaos':
                self._chaos = Chaos(self,val)
            elif name == 'post':
                self._post = PostXform(self,("coefs",val))          
            else:
                setattr(self,name,val)

        # Convert from "screen" to "complex plane" format
        self.d = -self.d
        self.b = -self.b
        self.f = -self.f
        
        # Create default values. Subclasses ignore this.
        if type(self) is Xform:
            if not self.chaos:
                self.chaos = Chaos(self,[1])
            if not self.post:
                self._post = PostXform(self,("coefs",[1,0,0,1,0,0]))    

    def _get_chaos(self):
        return self._chaos

    def _set_chaos(self,v):
        if type(v) is not Chaos:
            raise TypeError, "The chaos attribute requires a Chaos object"
        self._chaos = v

    chaos = property(_get_chaos,_set_chaos)    

    def _get_post(self):
        return self._post

    def _set_post(self,v):
        if type(v) is not PostXform:
            raise TypeError, "The post attribute requires a PostXform object"
        self._post = v

    post = property(_get_post,_set_post)

    def _get_coefs(self):
        return self.a,self.d,self.b,self.e,self.c,self.f

    def _set_coefs(self,v):
        self.a,self.d,self.b,self.e,self.c,self.f = v

    coefs = property(_get_coefs,_set_coefs)

    def get_screen_coefs(self):
        """Creates a list of coefs in "screen" notation."""
        return self.a,-self.d,-self.b,self.e,self.c,-self.f
        

#----------------------------------------------------------------------
    def _set_position(self,v1,v2=None):
        if v2 is None: v1, v2 = v1
        self.c = v1
        self.f = v2
        
    def _get_position(self):
        return self.c, self.f
    
    position = property(_get_position,_set_position)

    def move_position(self,v1,v2=None):
        if v2 is None: v1, v2 = v1       
        self.c += v1
        self.f += v2

#----------------------------------------------------------------------
    def _set_x(self,v1,v2=None):
        if v2 is None: v1, v2 = v1
        self.a  = v1 - self.c
        self.d  = v2 - self.f
        
    def _get_x(self):
        return self.a + self.c, self.d + self.f
    
    x = property(fget=_get_x,fset=_set_x)

    def move_x(self,v1,v2=None):     
        if v2 is None: v1, v2 = v1  
        self.a += v1
        self.d += v2

#----------------------------------------------------------------------
    def _set_y(self,v1,v2=None):
        if v2 is None: v1, v2 = v1
        self.b  = v1 - self.c
        self.e  = v2 - self.f
        
    def _get_y(self):
        return self.b + self.c, self.e + self.f

    y = property(fget=_get_y,fset=_set_y)

    def move_y(self,v1,v2=None):     
        if v2 is None: v1, v2 = v1 
        self.b += v1
        self.e += v2

#----------------------------------------------------------------------
    def _set_o(self,v1,v2=None):
        if v2 is None: v1, v2 = v1
        self.a += self.c - v1
        self.d += self.f - v2
        self.b += self.c - v1
        self.e += self.f - v2
        self.c  = v1
        self.f  = v2

    def _get_o(self):
        return self.c, self.f
    
    o = property(fget=_get_o,fset=_set_o)

    def move_o(self,v1,v2=None):
        if v2 is None: v1, v2 = v1
        self.a -= v1
        self.d -= v2
        self.b -= v1
        self.e -= v2
        self.c += v1
        self.f += v2

#----------------------------------------------------------------------
    def scale(self,v):
        self.a *= v
        self.d *= v
        self.b *= v
        self.e *= v

    def rotate(self,deg,pivot="local"):
        if pivot == "local":
            # Get the absolute angle each triangle leg will have after rotating. 
            # Atan2 puts the result into the proper quadrant automatically.
            angle   = radians(deg)
            x_angle = atan2(self.a,self.d) + angle
            y_angle = atan2(self.b,self.e) + angle
            
            # Get the length of the triangle leg, and reconstruct the
            # coordinate pair with the new angle.
            x_leg  = hypot(self.a,self.d)
            self.a = sin(x_angle) * x_leg
            self.d = cos(x_angle) * x_leg
            
            y_leg  = hypot(self.b,self.e)
            self.b = sin(y_angle) * y_leg
            self.e = cos(y_angle) * y_leg
        else:
            self.rotate(deg)
            self.orbit(deg,pivot)

    def orbit(self,deg,pivot=(0,0)):
        """Orbits the transform around a fixed point without rotating it."""
        hor = self.c - pivot[0]
        ver = self.f - pivot[1]   
        angle  = atan2(hor,ver) + radians(deg)
        
        vector = hypot(hor,ver)
        self.c = pivot[0] + sin(angle) * vector
        self.f = pivot[1] + cos(angle) * vector

    def copy(self):
        self._parent.xform.append(copy.deepcopy(self))

    def delete(self):
        if self._parent.final is self:
            self._parent.final = None            
        else:
            self._parent.xform.remove(self)

    def list_variations(self):
        return [i for i in variations if i in self.__dict__]

    def _get_attributes(self):
        return [i for i in self.__dict__ if i not in self._default]
    
    attributes = property(_get_attributes)

    def iter_attributes(self):
        return ((k,v) for (k,v) in self.__dict__.iteritems()
                if k not in self._default)




class PostXform(Xform):
    _allowed = ['coefs','_parent','a','b','c','d','e','f','x','y','o']
    
    def __repr__(self):
        xform = repr(self._parent)
        return "<post-%s" % xform[1:]

    def __setattr__(self,name,v):
        if name not in self._allowed:
            raise AttributeError, 'Can\'t assign "%s" to %s' %(name,self)
        object.__setattr__(self,name,v)

    def copy(self):
        raise TypeError, "Can't copy a post transform"

    def delete(self):
        raise TypeError, "Can't delete a post transform"    



class Chaos(list):
    """ A list which returns 1 for unassigned items, and pads the list when
    necessary to store values in their correct locations."""

    def __repr__(self):
        return str(self[:])

    def __init__(self,parent,lst):
        self._parent = parent
        lst.extend(1 for i in range(100-len(lst)))
        list.__init__(self,lst)

    def __len__(self):
        if self._parent is self._parent._parent.final:
            return 0
        return len(self._parent._parent.xform)

    def __iter__(self):
        return (self[i] for i in range(len(self)))
        
    def __getitem__(self,pos):
        if abs(pos) > len(self)-1:
            raise IndexError
        return list.__getitem__(self,pos)

    def __getslice__(self,pos,pos2):
        if (pos<0) or (pos2<0):
            raise NotImplementedError, "Negative slicing not supported"
        if pos2 > len(self): pos2 = len(self)
        return list.__getslice__(self,pos,pos2)
    
    def __setitem__(self,pos,val):
        if abs(pos) > len(self)-1:
            raise IndexError
        list.__setitem__(self,pos,val)
      
    def __setslice__(self,pos,pos2,val):
        if (pos<0) or (pos2<0):
            raise NotImplementedError, "Negative slicing not supported"
        list.__setslice__(self,pos,pos2,val)

    def get_list(self):
        lst = list.__getslice__(self,0,len(self))
        for i in reversed(lst):
            if i != 1: break
            lst.pop()
        return lst
