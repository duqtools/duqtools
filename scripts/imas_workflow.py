from duqtools.ids._location import ImasLocation

source = ImasLocation(db='jet', shot=92432, user='g2aho', run=1)

target = ImasLocation(db=source.db, shot=source.shot, run=1001)

source.copy_ids_entry_to(target)

core_profiles = target.get('core_profiles')

core_profiles.profiles_1d[0].t_i_average *= 1.1

with target.open() as data_entry_target:
    core_profiles.put(db_entry=data_entry_target)
