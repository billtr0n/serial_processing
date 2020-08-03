import os, re
import numpy as np
import matplotlib.pyplot as plt

def prune( d, pattern=None, types=None ):
    """
    @author: geoff ely
    Delete dictionary keys with specified name pattern or types
    Default types are: functions and modules.
    >>> prune( {'a': 0, 'a_': 0, '_a': 0, 'a_a': 0, 'b': prune} )
    {'a_a': 0}
    """
    if pattern == None:
        pattern = '(^_)|(_$)|(^.$)'
    if types is None:
        types = type( re ), type( re.sub )
    grep = re.compile( pattern )
    d2 = d.copy()
    for k in d.keys():
        if grep.search( k ) or type( d[k] ) in types:
            del( d2[k] )
    return d2


def parse( fd, prune_pattern=None, prune_types=None ):
    """ 
    @author: geoff ely (modified by william savran)
    parse vars in python file into new dict. ignore types and modules
    through prune types.
    
    inputs
    fd (string or file) : full_path or file

    returns
    parameters (dict) : containing parameter and its value. 
    """
    d = {}
    if isinstance(fd, str):
        fd = open( os.path.expanduser( fd ) )
    exec(fd.read(), d)
    prune( d, prune_pattern, prune_types )
    return d

def mw_to_m0( mw ):
    """ converts moment magnitude to moment using eq. 9.73 in shearer 2009 
    
    inputs
        mw (float) : moment magnitude
        
    return 
        m0 (float): seismic moment
    """
    return 10**(1.5*mw+9.1)

def poly_area(x,y):
    """ vectorized implementation of shoelace formula.

    inputs
        x (ndarray) : x coordinates of polygon
        y (ndarray) : y coordinates of polygon
        type : 'green' or 'shoe' indicating either using greens theorem or the shoelace formula

    returns
        area (float) : area of polygons in units of (x,y)
    """
    return 0.5*np.absolute(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

def poly_area_bbox(x,y):
    """ compute area based on bounding box around set of polygons. 

    inputs
        x (ndarray) : x coordinates of polygon
        y (ndarray) : y coordinates of polygon

    returns
        area (float) : area of polygon in units of (x,y)
    """
    minx = np.min(x)
    maxx = np.max(x)
    miny = np.min(y)
    maxy = np.max(y)
    bbox_area = (maxx-minx)*(maxy-miny)
    return bbox_area
    
def extract_from_string( string, prefix ):
    """ extract numeric value from string given prefix 
    
    inputs
        string : string to be searched
    prefix : substring(s), if list will append using '|'.  if both are in string
             will return from the first occurance.

    returns
        val : numeric value after prefix
    """
    # regex template
    template = "(?<=%s)\d+"
    if type(prefix) is list:
        s = '|'.join([template % p for p in prefix])
    else:
        s = template % prefix

    # im going to let this fail 
    val = re.search( s, string ).group()
    return val


def get_field_mask( sim, field, hypo_tol=4000, field_tol=0.001 ):
    """ 
    masks a rupture field around hypocenter, velocity strengthening region, and based on
    field values.  currently, masking where psv < 0.001 seems to be the most general approach.

    notes: returns the mask that is the same shape as 'field'

    inputs
        sim : simulation object
        field : string of field in simulation object to use.
        hypo_tol : radius to mask around hypocenter.
        vel_str_tol : velocity strengthening tolerance.
        field_tol : tolerance of simulation field.  

    return:
        field (ndarray.masked) 
    """
    # mask hypocentral area
    hx = int(sim.ihypo[0])
    hz = int(sim.ihypo[1])
    r = int(hypo_tol / sim.dx)
    z,x = np.ogrid[-hz:sim.nz-hz, -hx:sim.nx-hx]
    mask1 = x*x + z*z <= r*r

    # mask unruptured area
    field = getattr( sim, field )
    mask2 = np.zeros( sim.tsm[0,:,:].shape, dtype=bool )
    mask2[np.where( field < 0.001 )] = True

    # combine masks using logical or
    mask = np.ma.mask_or(mask1, mask2)
    
    return mask



# Depricated: Not working properly, although functionality might be useful later.
# def mask_from_polygon( sim, field, tol=25.0 ):
#     """ returns numpy mask given polygon vertices. 
    
#     inputs
#         sim : simulation object
#         field: name of field associated with sim 
        
#     returns
#         mask : 2d ndarray
#     """

#     from matplotlib.path import Path

#     data = getattr(sim, field)
#     nxiskp = sim.params['indices'][field][0][2]
#     nz,nx = data.shape

#     print nz, nx
#     dx = sim.dx * nxiskp
#     v = np.array([tol])
#     ex = nx*dx*1e-3
#     ez = nz*dx*1e-3
#     x = np.arange(0, ex, dx*1e-3)
#     z = np.arange(0, ez, dx*1e-3)
#     xx, zz = np.meshgrid(x, z)
#     ctrup = plt.contour(xx, zz, sim.trup, v)    

#     # convert back to cartesian
#     path = ctrup.collections[0].get_paths()[0]
#     grid = path.contains_points( np.vstack( (xx.flatten(), zz.flatten()) ).T )
#     grid = grid.reshape([ nz, nx ])
#     return grid


    
    
        
       
