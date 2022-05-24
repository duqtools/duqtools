from prepare_im_input import *
import numpy as np
from scipy import interpolate
from IPython import embed

# minimal example of taking Ti from a template run (with single IDS timeslice),
# modifying Ti profile by 10%, and saving IDSs into another location in the imasdb 

# uses functions from M. Marin prepare_im_input library

db = 'jet'
shot = 92432
user_source = 'g2aho'
run_source = 1
run_target = 1000 

copy_ids_entry(user_source, db, shot, run_source, shot, run_target) # create new IDS in user imasdb. Still same as template

# modify core profiles
core_profiles_mod = open_and_get_core_profiles(db, shot, run_source, user_source)
core_profiles_mod.profiles_1d[0].t_i_average *= 1.1

# modify IDS entry with new core_profiles
data_entry_target = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run_target)
op = data_entry_target.open()
core_profiles_mod.put(db_entry = data_entry_target)
data_entry_target.close()

#embed()
