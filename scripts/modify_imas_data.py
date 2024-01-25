from duqtools.api import ImasHandle

source = ImasHandle(db='jet', shot=94875, user='g2ssmee', run=8000)

target = ImasHandle(db=source.db, shot=source.shot, run=8888)

source.copy_data_to(target)

core_profiles = target.get('core_profiles')

core_profiles['profiles_1d/0/t_i_average'] *= 1.1

target.update_from(core_profiles)
