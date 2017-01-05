# python 
import os

# site-packages
import numpy as np

# local imports
import utils, tasks


class simulation( object ): 

    def __init__(self, dir_name):
        
        # intialize data structure to store simulation data
        self.data = {
          # from simulation configuration file
          'name': None,
          'friction': None,
          'rough_fault_seed': None,
          'fault_roughness': None,
          'ihypo': None,

          # calculated from simulation output
          'rupture_length'  : None,
          'rupture_area'    : None,
          'avg_stress_drop' : None,
          'avg_slip': None,
          'avg_psv' : None,
          'avg_surf_slip': None,
          'avg_surf_psv': None,
          'max_slip' : None,
          'max_psv' : None,
          'max_surf_slip' : None,
          'max_surf_psv' : None,
          'moment': None,
          'mw': None,
        }
        
        # populated from parsing the parameter file
        self.params = {}

        # hardcoded
        self.__config_file = 'meta.py'

        # simulation directory
        self.dir = os.path.expanduser( dir_name )

        # read simulation details and update data
        self.data.update( self.parse_simulation_details() )

        # add some parameters to top level class for easy access
        self.dt = self.params['dt']
        self.dx = self.params['dx'][0]
        self.nx = self.params['nn'][0]
        self.nz = self.params['nn'][1]
        self.ihypo = self.params['ihypo']
        self.name = self.params['name']

        # load slip, psv, and trup
        nx = self.params['shape']['su1'][0]
        nz = self.params['shape']['su1'][1]
        dtype = self.params['dtype']

        su1 = np.fromfile(os.path.join(self.dir, 'out/su1'), dtype=dtype).reshape([nz,nx])
        su2 = np.fromfile(os.path.join(self.dir, 'out/su2'), dtype=dtype).reshape([nz,nx])
        self.slip = np.sqrt( su1**2 + su2**2 )
        self.trup = np.fromfile(os.path.join(self.dir, 'out/trup'), dtype=dtype).reshape([nz,nx])
        self.psv = np.fromfile(os.path.join(self.dir, 'out/psv'), dtype=dtype).reshape([nz,nx])

        # load shear stress
        nx = self.params['shape']['tsm'][0]
        nz = self.params['shape']['tsm'][1]
        nt = self.params['shape']['tsm'][2] # some models didn't write out all timesteps

        self.tsm = np.fromfile( os.path.join(self.dir, 'out/tsm'), dtype=dtype )

        # sometimes the simulations finish early
        try:
            self.tsm = self.tsm.reshape([nt,nz,nx]) 
        except ValueError:
            n = len( self.tsm )
            sdim = n / ( nx * nz )
            self.tsm = self.tsm.reshape([sdim,nz,nx])

    def parse_simulation_details( self ):
        """ 
        parse parameters from meta.py file. will populate specifics for database.

        inputs
            config_file (string of file object) : configuration file for simulation
        
        returns
            params (dict) : params.keys() = ['name', 'friction', rough_fault_seed', 'fault_roughness']

        """ 
        # read meta.py file
        meta = utils.parse( os.path.join( self.dir, self.__config_file ) )

        # update simulation object with all parameters
        self.params.update( meta )

        # extract parameters
        data = {}
        data['name'] = meta['name']
        data['friction'] = meta['friction']
        data['rough_fault_seed'] = utils.extract_from_string( data['name'], ['rf','seed'] )
        data['fault_roughness'] = utils.extract_from_string( data['name'], 'a' )
        data['ihypo'] = str(meta['ihypo'])
        return data




    def get_masked_field(self, field_name, tind = None, mask='psv', tol=0.001, hypo_tol=4000):
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

        # get reference to fields
        field = getattr(self, field_name)
        mask_field = getattr(self, mask)
        
        nskipx_mask = self.params['indices'][mask][0][2]    
        if field_name is 'slip':
            nskipx_field = self.params['indices']['su1'][0][2]
        else:
            nskipx_field = self.params['indices'][field_name][0][2]
        

        # get dims of field
        nt = 0
        try:
            nx,nz,nt = field.shape
        except ValueError:
            nx,nz = field.shape

        # some sanity checks
        if len(mask_field.shape) > len(field.shape):
            raise ValueError("Mask should not have higher dimensionality that field being masked.")

        if mask_field.shape != (self.nz, self.nx):
            raise ValueError("Masking field should cover entire fault plane.  Try trup, or psv, or slip.")

        if nskipx_mask > nskipx_field:
            raise ValueError("Mask has less resolution that field. Unable to mask field.")

        # calculate hypocentral mask
        hx = int(self.ihypo[0])
        hz = int(self.ihypo[1])
        r = int(hypo_tol / self.dx)
        z,x = np.ogrid[-hz:self.nz-hz, -hx:self.nx-hx]
        mask1 = x*x + z*z <= r*r

        # mask unruptured area based on mask and tol
        mask2 = np.zeros( mask_field.shape, dtype=bool )
        mask2[np.where( mask_field < tol )] = True

        # decimate mask if necessary
        ratio = 1
        if nskipx_field != nskipx_mask:
            ratio = nskipx_field / nskipx_mask

        # combine masks using logical or
        mask = np.ma.mask_or(mask1, mask2)[::ratio, ::ratio]    

        # return at time
        if tind is not None:
            masked = np.ma.array( np.squeeze(field[tind, :, :]), mask = mask )
        else:
            masked = np.ma.array( field, mask = mask )

        return masked


    def process( self ):
        """ process the simulation from folders in tasks. make sure to update data as we go along. """
        
        print 'processing sim: %s' % self.name
        
        self.data['rupture_length'] = tasks.get_fault_extent( self )
        self.data['rupture_area'] = tasks.get_area( self )
        self.data['avg_stress_drop'] = tasks.compute_stress_drop( self )

        avg, avg_surf, mx, mx_surf = tasks.rupture_field_stats( self , 'slip' )
        self.data['avg_slip'] = avg
        self.data['avg_surf_slip']= avg_surf
        self.data['max_slip'] = mx
        self.data['max_surf_slip'] = mx_surf

        avg, avg_surf, mx, mx_surf = tasks.rupture_field_stats( self , 'psv' )
        self.data['avg_psv'] = avg
        self.data['avg_surf_psv'] = avg_surf
        self.data['max_psv'] = mx
        self.data['max_surf_psv'] = mx_surf

        self.data['mw'] = tasks.get_mw( self, self.params['dtype'] )
        self.data['moment'] = utils.mw_to_m0( self.data['mw'] )

        return self






