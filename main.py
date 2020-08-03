# python-packages
import os, traceback
import sys

# site-packages
import pandas as pd

# local imports
import tasks
from models import simulation

# read file containing list of directories to process
fpath_dirs_to_process = sys.argv[1]
if os.path.exists(fpath_dirs_to_process):
    with open(fpath_dirs_to_process, 'r') as f:
        dirs_to_process = [line.strip() for line in f.readlines()]
else:
    print("Error: list of simulation files not found")
    sys.exit(-1)

# process directories
data = []
for sim_dir in dirs_to_process:
    # only try directories with output folder
    subfolders = [ f.path for f in os.scandir(sim_dir) if f.is_dir() ]
    out_dir = os.path.join(sim_dir, 'out')
    if out_dir in subfolders:
          try:
                sim = simulation( sim_dir ).process()
                data.append( sim.data )
          except:
                print(f"error processing {sim_dir}. skipping.")
                traceback.print_exc()
    else:
        print(subfolders)
        # print(f"Warning: no output directory found in {sim_dir}. skipping.")

# put data into dataframe
d = pd.DataFrame( data )

# save to file
d.to_csv(os.path.expanduser('~/data_all_3.csv'))

