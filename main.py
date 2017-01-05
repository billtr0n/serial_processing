# python-packages
import os, traceback

# site-packages
import matplotlib.pyplot as plt 
import pandas as pd

# local imports
import tasks
from models import simulation


ens_dir = [os.path.expanduser('~/Dropbox/Current/simulations/rs_pla_tap_all'),
           os.path.expanduser('~/Dropbox/Current/simulations/5mpa_a005_mu0_0.225_eq_co_1mpa'),
           os.path.expanduser('~/Dropbox/Current/simulations/5mpa_a007_mu0_0.225_eq_co_1mpa'),
           os.path.expanduser('~/Dropbox/Current/simulations/sw_pla_tap_a007_s1_32_1d_all') ]

data = []
for ens in ens_dir:
      for root, dirs, files in os.walk( ens ):
            # only try directories with output folder
            if 'out' in dirs:
                  try:
                        sim = simulation( root ).process()
                        data.append( sim.data )
                  except:
                        print 'error processing %s. skipping.' % root



# put data into dataframe
d = pd.DataFrame( data )

# save to file
d.to_csv( os.path.expanduser( '~/Dropbox/Current/simulations/data_all_2.csv' ) )





