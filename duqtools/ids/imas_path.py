from .ids_location import ImasLocation

if __name__ == '__main__':

    source = ImasLocation(db='jet', shot=92432, user='g2aho', run=1)

    target = ImasLocation(db=source.db, shot=source.shot, run=1001)

    source.copy_ids_entry_to(target)

    core_profiles = target.get('core_profiles')

    # modify core profiles
    # core_profiles_mod = open_and_get_core_profiles(db, shot, run_source,
    #                                                user_source)
    # core_profiles_mod.profiles_1d[0].t_i_average *= 1.1

    # # modify IDS entry with new core_profiles
    # data_entry_target = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot,
    #                                  run_target)
    # op = data_entry_target.open()
    # core_profiles_mod.put(db_entry=data_entry_target)
    # data_entry_target.close()
