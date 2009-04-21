##############################################################################
#  The Combustion Flame Engine - pyflam3
#  http://combustion.sourceforge.net
#
#  Copyright (C) 2007 by Bobby R. Ward <bobbyrward@gmail.com>
#
#  The Combustion Flame Engine is free software; you can redistribute
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
from ctypes import *
from constants import *
from variations import *
import itertools
import sys

if 'win32' not in sys.platform:
    libflam3 = CDLL('libflam3.so')
    
else:
    try:
        libflam3 = CDLL('libflam3.dll')
        # VBT: Alternative?
##        libflam3 = WinDLL('libflam3.dll')
    except WindowsError:
        # Assume file not found
        import os.path
        # Find the win32_dlls sub directory
        this_dir = os.path.dirname(__file__)
        dll_dir = os.path.join(this_dir, 'win32_dlls')
        # Not add it to the PATH
        sys_path = os.environ['PATH']
        os.environ['PATH'] = ';'.join((sys_path, dll_dir))
        # Try again
        libflam3 = CDLL('libflam3.dll')

IteratorFunction = CFUNCTYPE(None, c_void_p, c_double)
SpatialFilterFunction = CFUNCTYPE(c_double, c_double)
ProgressFunction = CFUNCTYPE(c_int, POINTER(py_object), c_double, c_int, c_double)


def copy_to(src, dest):
    for (src_val, dest_val) in itertools.izip(src, dest):
        dest_val = src_val


class RandomContext(Structure):
    _fields_ = [ ('randcnt', c_ulong)
               , ('randrsl', c_ulong * flam3_RANDSIZ)
               , ('randmem', c_ulong * flam3_RANDSIZ)
               , ('randa', c_ulong)
               , ('randb', c_ulong)
               , ('randc', c_ulong)
               ]


class BaseImageComments(Structure): pass

class RenderStats(Structure): pass

class ImageStore(Structure): pass

class PaletteEntry(Structure):
    _fields_ = [('index', c_double),
                ('color', c_double * 4)]

class BasePalette(Structure):
    _fields_ = [('entries', PaletteEntry * 256)]

class BaseXForm(Structure): pass

class BaseGenome(Structure):
    _fields_ = [ ('name', c_char * (flam3_name_len + 1))
               , ('time', c_double)
               , ('interpolation', c_int)
               , ('interpolation_type', c_int)
               , ('palette_interpolation', c_int)
               , ('num_xforms', c_int)
               , ('final_xform_index', c_int)
               , ('final_xform_enable', c_int)
               , ('xform', POINTER(BaseXForm)) 
               , ('chaos', POINTER(c_double)) # what to do with this?
               , ('chaos_enable', c_int)
               , ('genome_index', c_int)
               , ('parent_fname', c_char * flam3_parent_fn_len)
               , ('symmetry', c_int)
               , ('palette', BasePalette)
               , ('input_image', c_char_p)
               , ('palette_index', c_int )      #TODO: Propertyize this(huh?)
               , ('brightness', c_double)
               , ('contrast', c_double)
               , ('gamma', c_double)
               , ('hihglight_power', c_double)
               , ('width', c_int )                  # wrapped
               , ('height', c_int )                 # wrapped
               , ('spatial_oversample', c_int )
               , ('_center', c_double * 2)          # wrapped
               , ('rot_center', c_double * 2)       # wrapped
               , ('rotate', c_double)           #TODO: Propertyize this
                                                #TODO: Add a angle version of the property
               , ('vibrancy', c_double)
               , ('hue_rotation', c_double)
               , ('background', c_double * 3)   #TODO: Propertyize this
               , ('zoom', c_double)
               , ('pixels_per_unit', c_double)
               , ('spatial_filter_radius', c_double)
               , ('spacial_filter_select', c_int)
               , ('sample_density', c_double)
               , ('nbatches', c_int)
               , ('ntemporal_samples', c_int)
               , ('estimator', c_double)
               , ('estimator_curve', c_double)
               , ('estimator_minimum', c_double)
               , ('edits', py_object) # or c_void_p?
               , ('gam_lin_thresh', c_double)
               , ('palette_index0', c_int)
               , ('hue_rotation0', c_double)
               , ('palette_index1', c_int)
               , ('hue_rotation1', c_double)
               , ('palette_blend', c_double)
               , ('temporal_filter_type', c_int)
               , ('temporal_filter_width', c_double)
               , ('temporal_filter_exp', c_double)
               , ('palette_mode', c_int)
               ]


class BaseFrame(Structure):
    _fields_ = [ #('temporal_filter_radius', c_double)
                ('pixel_aspect_ratio', c_double)
               , ('genomes', POINTER(BaseGenome))
               , ('ngenomes', c_int)
               , ('verbose', c_int)
               , ('bits', c_int)
               , ('bytes_per_channel', c_int)
               , ('earlyclip', c_int)
               , ('time', c_double)
               , ('progress', ProgressFunction) 
               , ('progress_parameter', py_object) # or c_void_p?
               , ('rc', RandomContext) 
               , ('nthreads', c_int)
               ]


def allocate_output_buffer(size, channels):
    return (c_ubyte * (size[0] * size[1] * channels))()

#-----------------------------------------------------------------------------
# VBT: This function is needed to make a direct call to flam3_iterate work.

#void prepare_xform_fn_ptrs(flam3_genome *cp, randctx *rc)
libflam3.prepare_xform_fn_ptrs.argtypes = [POINTER(BaseGenome), POINTER(RandomContext)]
prepare_xform_fn_ptrs = libflam3.prepare_xform_fn_ptrs

#-----------------------------------------------------------------------------

# void flam3_print(FILE *f, flam3_genome *g, char *extra_attributes, int print_edits);
libflam3.flam3_print.argtypes = [c_void_p, POINTER(BaseGenome), c_char_p, c_int]
flam3_print = libflam3.flam3_print 

# flam3_genome *flam3_parse_from_file(FILE *f, char *fn, int default_flag, int *ncps);
libflam3.flam3_parse_from_file.argtypes = [c_void_p, c_char_p, c_int, POINTER(c_int)]
libflam3.flam3_parse_from_file.restype = POINTER(BaseGenome)
flam3_parse_from_file = libflam3.flam3_parse_from_file

# char *flam3_version();
libflam3.flam3_version.restype = c_char_p
flam3_version = libflam3.flam3_version

# int flam3_get_palette(int palette_index, flam3_palette p, double hue_rotation);
libflam3.flam3_get_palette.restype = c_int
libflam3.flam3_get_palette.argtypes = [c_int, POINTER(BasePalette), c_double]
flam3_get_palette = libflam3.flam3_get_palette

# extern char *flam3_variation_names[];
flam3_variation_names = (c_char_p * flam3_nvariations).in_dll(libflam3, 'flam3_variation_names')

# void flam3_add_xforms(flam3_genome *cp, int num_to_add);
libflam3.flam3_add_xforms.argtypes = [POINTER(BaseGenome), c_int]
flam3_add_xforms = libflam3.flam3_add_xforms

# void flam3_delete_xform(flam3_genome *thiscp, int idx_to_delete);
libflam3.flam3_delete_xform.argtypes = [POINTER(BaseGenome), c_int]
flam3_delete_xform = libflam3.flam3_delete_xform

# void flam3_copy(flam3_genome *dest, flam3_genome *src);
libflam3.flam3_copy.argtypes = [POINTER(BaseGenome), POINTER(BaseGenome)]
flam3_copy = libflam3.flam3_copy

# void flam3_copyx(flam3_genome *dest, flam3_genome *src, int num_std, int num_final);
libflam3.flam3_copyx.argtypes = [POINTER(BaseGenome), POINTER(BaseGenome), c_int, c_int]
flam3_copyx = libflam3.flam3_copyx

# void flam3_copy_params(flam3_xform *dest, flam3_xform *src, int varn);
libflam3.flam3_copy_params.argtypes = [POINTER(BaseXForm), POINTER(BaseXForm), c_int]
flam3_copy_params = libflam3.flam3_copy_params

# void flam3_create_xform_distrib(flam3_genome *cp, unsigned short *xform_distrib);
libflam3.flam3_create_xform_distrib.argtypes = [POINTER(BaseGenome), POINTER(c_ushort)]
flam3_create_xform_distrib = libflam3.flam3_create_xform_distrib

# int flam3_iterate(flam3_genome *g, int nsamples, int fuse, double *samples, unsigned short *xform_distrib, randctx *rc);
libflam3.flam3_iterate.argtypes = [POINTER(BaseGenome), c_int, c_int, POINTER(c_double), POINTER(c_ushort), POINTER(RandomContext)]
libflam3.flam3_iterate.restype = c_int
flam3_iterate = libflam3.flam3_iterate

# void flam3_interpolate(flam3_genome *genomes, int ngenomes, double time, flam3_genome *result);
libflam3.flam3_interpolate.argtypes = [POINTER(BaseGenome), c_int, c_double, POINTER(BaseGenome)]
flam3_interpolate = libflam3.flam3_interpolate

# void flam3_interpolate_n(flam3_genome *result, int ncp, flam3_genome *cpi, double *c);
libflam3.flam3_interpolate_n.argtypes = [POINTER(BaseGenome), c_int, POINTER(BaseGenome), POINTER(c_double)]
flam3_interpolate_n = libflam3.flam3_interpolate_n

# void flam3_random(flam3_genome *g, int *ivars, int ivars_n, int sym, int spec_xforms);
libflam3.flam3_random.argtypes = [POINTER(BaseGenome), POINTER(c_int), c_int, c_int, c_int]
flam3_random = libflam3.flam3_random

# char *flam3_print_to_string(flam3_genome *cp);
libflam3.flam3_print_to_string.argtypes = [POINTER(BaseGenome)]
libflam3.flam3_print_to_string.restype = c_char_p
flam3_print_to_string = libflam3.flam3_print_to_string

# flam3_genome *flam3_parse_xml2(char *s, char *fn, int default_flag, int *ncps);
libflam3.flam3_parse_xml2.argtypes = [c_char_p, c_char_p, c_int, POINTER(c_int)]
libflam3.flam3_parse_xml2.restype = POINTER(BaseGenome)
flam3_parse_xml2 = libflam3.flam3_parse_xml2

# void flam3_add_symmetry(flam3_genome *g, int sym);
libflam3.flam3_add_symmetry.argtypes = [POINTER(BaseGenome), c_int]
flam3_add_symmetry = libflam3.flam3_add_symmetry

# void flam3_parse_hexformat_colors(char *colstr, flam3_genome *cp, int numcolors, int chan);
libflam3.flam3_parse_hexformat_colors.argtypes = [c_char_p, POINTER(BaseGenome), c_int, c_int]
flam3_parse_hexformat_colors = libflam3.flam3_parse_hexformat_colors

# void flam3_estimate_bounding_box(flam3_genome *g, double eps, int nsamples, double *bmin, double *bmax, randctx *rc);
libflam3.flam3_estimate_bounding_box.argtypes = [POINTER(BaseGenome), c_double, c_int, POINTER(c_double), POINTER(c_double), POINTER(RandomContext)]
flam3_estimate_bounding_box = libflam3.flam3_estimate_bounding_box

# void flam3_rotate(flam3_genome *g, double angle); 
libflam3.flam3_rotate.argtypes = [POINTER(BaseGenome), c_double]
flam3_rotate = libflam3.flam3_rotate

# double flam3_dimension(flam3_genome *g, int ntries, int clip_to_camera);
libflam3.flam3_dimension.argtypes = [POINTER(BaseGenome), c_int, c_int]
libflam3.flam3_dimension.restype = c_double
flam3_dimension = libflam3.flam3_dimension

# double flam3_lyapunov(flam3_genome *g, int ntries);
libflam3.flam3_lyapunov.argtypes = [POINTER(BaseGenome), c_int]
libflam3.flam3_lyapunov.restype = c_double
flam3_lyapunov = libflam3.flam3_lyapunov

# void flam3_apply_template(flam3_genome *cp, flam3_genome *templ);
libflam3.flam3_apply_template.argtypes = [POINTER(BaseGenome), POINTER(BaseGenome)]
flam3_apply_template = libflam3.flam3_apply_template

# int flam3_count_nthreads(void);
libflam3.flam3_count_nthreads.restype = c_int
flam3_count_nthreads = libflam3.flam3_count_nthreads

# void flam3_render(flam3_frame *f, unsigned char *out, int out_width, int field, int nchan, int transp, stat_struct *stats);
libflam3.flam3_render.argtypes = [POINTER(BaseFrame), POINTER(c_ubyte), c_int, c_int, c_int, c_int, POINTER(RenderStats)]
flam3_render = libflam3.flam3_render

# double flam3_render_memory_required(flam3_frame *f);
libflam3.flam3_render_memory_required.argtypes = [POINTER(BaseFrame)]
libflam3.flam3_render_memory_required.restype = c_double
flam3_render_memory_required = libflam3.flam3_render_memory_required

# double flam3_random01();
libflam3.flam3_random01.restype = c_double
flam3_random01 = libflam3.flam3_random01

# double flam3_random11();
libflam3.flam3_random11.restype = c_double
flam3_random11 = libflam3.flam3_random11

# int flam3_random_bit();
libflam3.flam3_random_bit.restype = c_int
flam3_random_bit = libflam3.flam3_random_bit

# double flam3_random_isaac_01(randctx *);
libflam3.flam3_random_isaac_01.argtypes = [POINTER(RandomContext)]
libflam3.flam3_random_isaac_01.restype = c_double
flam3_random_isaac_01 = libflam3.flam3_random_isaac_01

# double flam3_random_isaac_11(randctx *);
libflam3.flam3_random_isaac_11.argtypes = [POINTER(RandomContext)]
libflam3.flam3_random_isaac_11.restype = c_double
flam3_random_isaac_11 = libflam3.flam3_random_isaac_11

# int flam3_random_isaac_bit(randctx *);
libflam3.flam3_random_isaac_bit.argtypes = [POINTER(RandomContext)]
libflam3.flam3_random_isaac_bit.restype = c_double
flam3_random_isaac_bit = libflam3.flam3_random_isaac_bit

# void flam3_init_frame(flam3_frame *f);
libflam3.flam3_init_frame.argtypes = [POINTER(BaseFrame)]
flam3_init_frame = libflam3.flam3_init_frame

### size_t flam3_size_flattened_genome(flam3_genome *cp);
##libflam3.flam3_size_flattened_genome.argtypes = [POINTER(BaseGenome)]
##libflam3.flam3_size_flattened_genome.restype = c_ulong
##flam3_size_flattened_genome = libflam3.flam3_size_flattened_genome

### void flam3_flatten_genome(flam3_genome *cp, void *buf);
##libflam3.flam3_flatten_genome.argtypes = [POINTER(BaseGenome), c_void_p]
##flam3_flatten_genome = libflam3.flam3_flatten_genome

### void flam3_unflatten_genome(void *buf, flam3_genome *cp);
##libflam3.flam3_unflatten_genome.argtypes = [c_void_p, POINTER(BaseGenome)]
##flam3_unflatten_genome = libflam3.flam3_unflatten_genome

# void write_png(FILE *file, unsigned char *image, int width, int height, flam3_img_comments *fpc);
libflam3.write_png.argtypes = [c_void_p, POINTER(c_ubyte), c_int, c_int, POINTER(BaseImageComments)]
write_png = libflam3.write_png

# void write_jpeg(FILE *file, unsigned char *image, int width, int height, flam3_img_comments *fpc);
libflam3.write_jpeg.argtypes = [c_void_p, POINTER(c_ubyte), c_int, c_int, POINTER(BaseImageComments)]
write_jpeg = libflam3.write_jpeg

# void flam3_align(flam3_genome *dst, flam3_genome *src, int nsrc);
libflam3.flam3_align.argtypes = [POINTER(BaseGenome), POINTER(BaseGenome), c_int]

flam3_malloc = libflam3.flam3_malloc
flam3_malloc.argtypes = [c_int]
flam3_malloc.restype = c_void_p

flam3_free = libflam3.flam3_free
flam3_free.argtypes = [c_void_p]




