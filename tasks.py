import os
import numpy as np
import matplotlib.pyplot as plt
import utils

def get_fault_extent( sim, tol=20.0 ):
    """ calculates fault length based on a simple triggering algorithm. 
        along dip average of trup is compared with 'tol' and triggered
        accordingly. current formulation only works with monotonically increasing
        fields, e.g. trup. with something like slip or psv that tends to zero outside the fault, 
        the trigger happens with the 'less-than' comparison for both ends.
        
	inputs 
	    trup (2d ndarray) : rupture time field on fault
	    tol (float)       : time tolerance (s) used to calculate contour
	    nx (int)          : number of nodes along strike 
	    nz (int)          : number of nodes along dip
	    dx (float)        : simulation spacing (km)

	returns 
            length (float)      : fault length (km)
    """
    trigger = False
    minx=0
    maxx=sim.nx*sim.dx
    for i in range(sim.nx):
        dslice = sim.trup[:,i]
        avg = np.median(dslice)
        if avg < tol and not trigger:
            trigger = True
            minx = i*sim.dx
        if trigger and avg >= tol:
            trigger = False
            maxx = i*sim.dx
    return maxx-minx

def get_area( sim, tol=20.0 ):
    """ calculates area based on shoelace formula and contour. 
	calculate contour of trup at the end of the rupture and integrate
	polyhedra using shoelace formula.

	inputs 
            sim : simulation object 
            tol : tolerance for contour

	returns 
            area (float)      : simulation area (km^2)
    """
    v = np.array([tol])
    ex = sim.nx*sim.dx*1e-3
    ez = sim.nz*sim.dx*1e-3
    x = np.arange(0, ex, sim.dx*1e-3)
    z = np.arange(0, ez, sim.dx*1e-3)
    xx, zz = np.meshgrid(x, z)
    ctrup = plt.contour(xx, zz, sim.trup, v, extent= (0, ex, 0, ez))	
    xz = []
    for pp in ctrup.collections[0].get_paths():
        for vv in pp.iter_segments():
            xz.append(vv[0])
    # sort coordinates according to theta
    xz = np.array( xz ) 
    return utils.poly_area(xz[:,0], xz[:,1])

def get_area_bbox( sim, tol=1e-5, top_start = 4000 ):
    """ calculates area based on bounding box around the ruptured surface. 

	inputs 
            sim : simulation object 
            tol : tolerance for contour

	returns 
            area (float)      : simulation area (km^2)
    """
    # define fault coordinates
    ex = sim.nx*sim.dx*1e-3
    ez = sim.nz*sim.dx*1e-3
    x = np.arange(0, ex, sim.dx*1e-3)
    z = np.arange(0, ez, sim.dx*1e-3)
    istart = int(np.rint(top_start / sim.dx))

    minx = 0 
    maxx = ex
    trigger = False
    for i in range(sim.nx):
        dslice = sim.slip[istart:,i]
        min_slip = np.max(dslice)
        if not trigger and min_slip > 0.25:
            trigger = True
            minx = i*sim.dx*1e-3
        elif trigger and min_slip <= 0.25:
            maxx = i*sim.dx*1e-3
            trigger = False
            break
    length = maxx-minx

    minz=0
    maxz=ez
    trigger=False
    for j in range(sim.nz):
        hslice = sim.slip[j,:]
        min_slip = np.max(hslice)
        if not trigger and min_slip > 0.25:
            trigger = True
            minz = j*sim.dx*1e-3
        elif trigger and min_slip <= 0.25:
            maxz = j*sim.dx*1e-3
            trigger = False
            break
    width = maxz-minz
    print(f"length: {length}, width: {width}")
    return length*width


def get_mw( sim, dtype='<f4' ):
    """ reading mw from file 
    
    inputs
        sim : simulation object 

    returns
        m0 (float) : seismic moment in Nm
    """
    fp = os.path.join(sim.dir, 'stats/mw')
    if not os.path.exists(fp):
        fp = os.path.join(sim.dir, 'stats.old/mw')
    mw = np.fromfile(fp, dtype=dtype)
    return mw[-1]

def compute_stress_drop( sim, tol=0.001 ): 
    """ computes stress drop from shear stress file.  by tsm[time=end] - tsm[time=start]

    inputs
        sim : simulation object 

    returns
        stress_drop : stress drop averaged over model
    """ 
    
    # ind for velocity str region
    tsm_start = sim.get_masked_field( 'tsm', tind = 0 )
    tsm_end = sim.get_masked_field( 'tsm' , tind = -1 )

    # return average stress drop
    delt = tsm_end - tsm_start
    return np.mean(delt) / 1e6


def rupture_field_stats( sim, field_name ):
    """ computes rupture field statistics

    inputs
	field : 2d ndarray where surf is ind = 0
        dx : simulation grid spacing in meters
        ihypo : hypocenter indices

    returns
        (avg, avg_surf, max, max_surf) : statistics from rupture field
    """ 

    # get necessary indices
    
    field = getattr( sim, field_name )

    field_masked = sim.get_masked_field( field_name )

    return ( field_masked.mean(), 
             field_masked[0,:].mean(), 
             field_masked.max(), 
             field_masked[0,:].max() )
    	

    
