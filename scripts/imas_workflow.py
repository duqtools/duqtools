from duqtools.ids.ids_location import ImasLocation

source = ImasLocation(db='jet', shot=92432, user='g2aho', run=1)

target = ImasLocation(db=source.db, shot=source.shot, run=1001)

source.copy_ids_entry_to(target)

core_profiles = target.get('core_profiles')

core_profiles.profiles_1d[0].t_i_average *= 1.1

data_entry_target = target.entry()

op = data_entry_target.open()

core_profiles.put(db_entry=data_entry_target)

data_entry_target.close()
