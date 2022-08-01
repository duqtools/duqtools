import json
import os,datetime,sys
import shutil
import getpass
import numpy as np
import pickle
import math
import functools
import copy
from scipy import integrate
from scipy.interpolate import interp1d, UnivariateSpline
#from extra_tools_im import *
#import idstools
#from idstools import *
from packaging import version
from os import path
import inspect
import types
#All the keys needed to map the structure in the dictionary are stored here
#from keys_lists import *

import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation
from IPython import display

import xml.sax
import xml.sax.handler

min_imas_version_str = "3.28.0"
min_imasal_version_str = "4.7.2"

try:
    import imas
except ImportError:
    warnings.warn("IMAS Python module not found or not configured properly, tools need IDS to work!", UserWarning)
if imas is not None:
    from imas import imasdef
    vsplit = imas.names[0].split("_")
    imas_version = version.parse(".".join(vsplit[1:4]))
    ual_version = version.parse(".".join(vsplit[5:]))
    if imas_version < version.parse(min_imas_version_str):
        raise ImportError("IMAS version must be >= %s! Aborting!" % (min_imas_version_str))
    if ual_version < version.parse(min_imasal_version_str):
        raise ImportError("IMAS AL version must be >= %s! Aborting!" % (min_imasal_version_str))

'''
--------------- AVAILABLE FUNCTIONS: ------------------

1 - setup_input_baserun(db, shot, run_exp, run_input, zeff_option = None, instructions = [], time_start = 0, time_end = 100)
'''

def setup_input(db, shot, run_input, run_start, zeff_option = None, zeff_mult = 1, instructions = [], boundary_instructions = {}, time_start = 0, time_end = 100, verbose = False, core_profiles = None, equilibrium = None):

    '''

    Instructions is a list of strings with a list of actions that should be performed.
    Possibilities are: average, rebase, nbi heating, flat q profile, correct zeff, correct boundaries, flipping ip

    zeff_option needs a string with a key word about what to do with zeff.
    Possibilities are: None, flat maximum, flat minimum, flat median, impurity from flattop. Correct zeff is an extra action, needs to be in istructions

    '''
    username = getpass.getuser()
    average, rebase, nbi_heating, flat_q_profile = False, False, False, False
    correct_Zeff, set_boundaries, correct_boundaries, adding_early_profiles = False, False, False, False

    # To save computational time, equilibrium and core profiles might be passed if they have already been extracted

    if not core_profiles:
        core_profiles = open_and_get_core_profiles(db, shot, run_input)
    if not equilibrium:
        equilibrium = open_and_get_equilibrium(db, shot, run_input)
        print('opening the equilibrium here')

    if boundary_instructions:
        boundary_method = boundary_instructions['method']
        boundary_sep_te = boundary_instructions['te_sep']
        boundary_sep_ti = None
        if 'ti_sep' in boundary_instructions:
            boundary_sep_ti = boundary_instructions['ti_sep']

    ip = equilibrium.time_slice[0].global_quantities.ip
    b0 = equilibrium.vacuum_toroidal_field.b0

    flipping_ip = False
    if ip > 0:
        instructions.append('flipping ip')
        print('ip will be flipped. Still necessary because of bugs but should not happen')

    if average and rebase:
        print('rebase and average cannot be done at the same time. Aborting')
        exit()

    if zeff_option:
        for index in range(run_start - len(instructions), run_start, 1):
            data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, index, user_name=username)
            op = data_entry.open()

            if op[0]==0:
                print('One of the data entries needed to manipulate the input already exists, aborting. Try increasing run start.')
                exit()

            data_entry.close()

    else:
        for index in range(run_start - len(instructions) + 1, run_start, 1):
            data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, index, user_name=username)
            op = data_entry.open()

            if op[0]==0:
                print('One of the data entries needed to manipulate the input already exists, aborting. Try increasing run start.')
                exit()

            data_entry.close()

    run_start = run_start - len(instructions) + 1
    if zeff_option is not None:
        run_start = run_start - 1

    time_eq = equilibrium.time
    time_cp = core_profiles.time

    if time_start == None:
        time_start = max(min(time_eq), min(time_cp))
    elif time_start == 'core_profile':
        time_start = min(time_cp)
    elif time_start == 'equilibrium':
        time_start = min(time_eq)
    else:
        time_start = time_start

    if 'average' in instructions:
        average_integrated_modelling(db, shot, run_input, run_start, time_start, time_end)
        print('Averaging on index ' + str(run_start))
        run_input, run_start = run_start, run_start+1

    # Rebase sets the times of the equilibrium equal to the times in core profiles. Usually the grid in core profiles is more coarse.
    # This should help with the speed and with the noisiness in vloop

    elif 'rebase' in instructions:
        rebase_integrated_modelling(db, shot, run_input, run_start, time_cp, ['equilibrium'])
        print('Rebasing on index ' + str(run_start))
        run_input, run_start = run_start, run_start+1

    # If necessary, flipping ip here. Runs for sensitivities should be possible from this index (unless Zeff is weird)

    if 'flipping ip' in instructions:

        # Currently flips both Ip and b0
        flip_ip(db, shot, run_input, shot, run_start)
        print('flipping ip on index ' + str(run_start))
        run_input, run_start = run_start, run_start+1

        # option of flipping the q profile might be added here
        #flip_q_profile(db, shot, run_input, run_start)
        #print('flipping q profile on index ' + str(run_start))
        #run_input, run_start = run_start, run_start+1


    # Temporarily like this. The function itself will need to be updated
    if 'nbi heating' in instructions:
        prepare_nbi(db, shot, run_input, shot, run_start)
        print('Preparing nbi on index ' + str(run_start))
        run_input, run_start = run_start, run_start+1

    ion_number = check_ion_number(db, shot, run_input)

    if 'set boundaries' in instructions:
        set_boundaries_te(db, shot, run_input, run_start, te_sep = boundary_sep_te, ti_sep = boundary_sep_ti, method = boundary_method)
        print('Setting boundaries te and ti on index ' + str(run_start))
        run_input, run_start = run_start, run_start + 1

    if 'correct boundaries' in instructions:
        correct_boundaries_te(db, shot, run_input, db, shot, run_start)
        print('Correcting te at the boundaries on index ' + str(run_start))
        run_input, run_start = run_start, run_start+1

    if 'add early profiles' in instructions:

        add_early_profiles(db, shot, run_input, run_start)
        print('Adding early profiles on index ' + str(run_start))
        run_input, run_start = run_start, run_start+1

    if zeff_option is not None:
        if zeff_option == 'flat maximum':
            set_flat_Zeff(db, shot, run_input, run_start, 'maximum')
            print('Setting flat Zeff with maximum value on index ' + str(run_start))
            run_input, run_start = run_start, run_start+1
        elif zeff_option == 'flat minimum':
            set_flat_Zeff(db, shot, run_input, run_start, 'minimum')
            print('Setting flat Zeff with minimum value on index ' + str(run_start))
            run_input, run_start = run_start, run_start+1
        elif zeff_option == 'flat median':
            set_flat_Zeff(db, shot, run_input, run_start, 'median')
            print('Setting flat Zeff with median value on index ' + str(run_start))
            run_input, run_start = run_start, run_start+1
        elif zeff_option == 'parabolic':
            set_parabolic_zeff(db, shot, run_input, run_start, zeff_mult = zeff_mult)
            print('Setting parabolic zeff profile on index ' + str(run_start))
            run_input, run_start = run_start, run_start+1
        elif ion_number > 1 and not average and zeff_option == 'impurity from flattop':
            set_impurity_composition_from_flattop(db, shot, run_input, run_start, verbose = verbose)
            print('Setting impurity composition from flattop on index ' + str(run_start))
            run_input, run_start = run_start, run_start+1
        elif ion_number > 1 and average and zeff_option == 'impurity from flattop':
            print('Cannot extract the impurities from flattop when averaging')
            exit()
        elif ion_number > 1 and not average and zeff_option == 'linear descending zeff':
            set_linear_descending_zeff(db, shot, run_input, run_start)
            print('Setting descending initial impurity composition on index ' + str(run_start))
            run_input, run_start = run_start, run_start+1
        elif ion_number > 1 and not average and zeff_option == 'ip ne scaled':
            set_ip_ne_scaled_zeff(db, shot, run_input, run_start)
            print('Setting impurity composition using ne and ip scaling on index ' + str(run_start))
            run_input, run_start = run_start, run_start+1
        elif ion_number > 1 and not average and zeff_option == 'hyperbole':
            set_hyperbole_zeff(db, shot, run_input, run_start)
            print('Setting descending hiperbolic initial impurity composition on index ' + str(run_start))
            run_input, run_start = run_start, run_start+1
        else:
            print('Option for Zeff initialization not recognized. Aborting generation')
            exit()

    if 'parabolic zeff' in instructions:
        set_parabolic_zeff(db, shot, run_input, run_start, zeff_mult = zeff_mult)
        print('Setting parabolic zeff profile on index ' + str(run_start))
        run_input, run_start = run_start, run_start+1
    elif 'peaked zeff' in instructions:
        set_peaked_zeff_profile(db, shot, run_input, run_start, zeff_mult = zeff_mult)
        print('Setting peaked zeff profile on index ' + str(run_start))
        run_input, run_start = run_start, run_start+1
    elif 'parabolic zeff' in instructions and 'peaked zeff' in instructions:
        print('zeff profiles cannot be peaked and parabolic at the same time. Aborting')
        exit()


    if 'correct zeff' in instructions:
        correct_zeff(db, shot, run_input, db, shot, run_start)
        print('correcting zeff on index ' + str(run_start))
        run_input, run_start = run_start, run_start+1

    if 'flat q profile' in instructions:
        use_flat_q_profile(db, shot, run_input, run_start)
        print('setting a flat q profile on index ' + str(run_start))
        run_input, run_start = run_start, run_start+1

    # To save time, core_profiles and equilibrium are saved and passed

    return core_profiles, equilibrium


class IntegratedModellingDict:

    def __init__(self, db, shot, run, username='', backend='mdsplus'):

        # It might be possible to generalize part of the following functions. Left for future work
        # The extraction might also be simplified using partial_get. I am not sure if the filling part can also be simplified...

        # ------------------------------ LITS WITH ALL THE KEYS -----------------------------------
        self.all_keys = copy.deepcopy(keys_list)
        self.ids_struct = open_integrated_modelling(db, shot, run, username=username, backend=backend)
        self.extract_ids_dict()

    def extract_ids_dict(self):
    
        self.ids_dict = {'time' : {}, 'traces' : {}, 'profiles_1d' : {}, 'profiles_2d' : {}, 'extras' : {}}
    
        # -------------------- Extract summary -----------------------------------
    
        traces, time = self.extract_summary()
    
        self.ids_dict['traces'] = {**self.ids_dict['traces'], **traces}
        self.ids_dict['time']['summary'] = time
    
        # -------------------- Extract core profiles -----------------------------
    
        #Maybe also everything in grid?
    
        profiles_1d, traces, time = self.extract_core_profiles()
    
        self.ids_dict['profiles_1d'] = {**self.ids_dict['profiles_1d'], **profiles_1d}
        self.ids_dict['traces'] = {**self.ids_dict['traces'], **traces}
        self.ids_dict['time']['core_profiles'] = time
    
        # --------------------- Extract equilibrium ------------------------------
    
        profiles_2d, profiles_1d, traces, extras, time = self.extract_equilibrium()

        self.ids_dict['profiles_2d'] = {**self.ids_dict['profiles_2d'], **profiles_2d}
        self.ids_dict['profiles_1d'] = {**self.ids_dict['profiles_1d'], **profiles_1d}
        self.ids_dict['traces'] = {**self.ids_dict['traces'], **traces}
        self.ids_dict['extras'] = {**self.ids_dict['extras'], **extras}         # Might not need this one when new_classes actually becomes a class
        self.ids_dict['time']['equilibrium'] = time
    
        # --------------------- Extract core_sources ----------------------------
    
        profiles_1d, traces, time = self.extract_core_sources()
    
        self.ids_dict['profiles_1d'] = {**self.ids_dict['profiles_1d'], **profiles_1d}
        self.ids_dict['traces'] = {**self.ids_dict['traces'], **traces}
        self.ids_dict['time']['core_sources'] = time
    
        # --------------------- Extract nbi data --------------------------------
        '''
        profiles_1d, traces, time = self.extract_nbi()
    
        self.ids_dict['profiles_1d'] = {**self.ids_dict['profiles_1d'], **profiles_1d}
        self.ids_dict['traces'] = {**self.ids_dict['traces'], **traces}
        self.ids_dict['time']['nbi'] = time
        '''
        # Pellets maybe in the future
    
    def extract_core_profiles(self):
    
        profiles_1d, traces = {}, {}
        ids_iden = 'core_profiles'
    
        for tag in keys_list['profiles_1d']['core_profiles']:
            parts = tag.split('[')
            # Initializing profiles
            if len(parts) == 1:
                profiles_1d[tag] = []
            elif len(parts) == 2:
    
                # A new list needs to be created, appending the keys including the values of the indexes of the nested elements
                self.all_keys['profiles_1d']['core_profiles'].append(parts[0] + '[' + str(0) + parts[1])
                profiles_1d[parts[0] + '[' + str(0) + parts[1]] = []
    
            # Filling profiles
            for profile in self.ids_struct[ids_iden].profiles_1d:
                parts = tag.split('[')
                if len(parts) == 1:
                    point = eval('profile.' + tag)
                    profiles_1d[tag].append(point)
    
            for profile in self.ids_struct[ids_iden].profiles_1d:
                if len(parts) == 2:
    
                    array = eval('profile.' + parts[0])
                    for index, element in enumerate(array):
                        point = eval('element.' + parts[1][2:])
                        if parts[0] + '[' + str(index) + parts[1] not in profiles_1d:
                            self.all_keys['profiles_1d']['core_profiles'].append(parts[0] + '[' + str(index) + parts[1])  # adding the keys
                            profiles_1d[parts[0] + '[' + str(index) + parts[1]] = [point]
                        else:
                            profiles_1d[parts[0] + '[' + str(index) + parts[1]].append(point)
    
        # The values need to be arrays, not lists
        for key in profiles_1d:
            profiles_1d[key] = np.asarray(profiles_1d[key])
    
        for tag in keys_list['traces']['core_profiles']:
            parts = tag.split('[')
            if len(parts) == 1:
                traces[tag] = eval('self.ids_struct[ids_iden].global_quantities.'+ tag)
                traces[tag] = np.asarray(traces[tag])
    
            if len(parts) == 2:
                for profile in self.ids_struct[ids_iden].profiles_1d:
                    array = eval('profile.' + parts[0])
                    for index, element in enumerate(array):
                        point = eval('element.' + parts[1][2:])
                        if parts[0] + '[' + str(index) + parts[1] not in traces:
                            self.all_keys['traces']['core_profiles'].append(parts[0] + '[' + str(index) + parts[1])  # adding the keys
                            traces[parts[0] + '[' + str(index) + parts[1]] = [point]
                        else:
                            traces[parts[0] + '[' + str(index) + parts[1]].append(point)

                # atoms_n and multiple_states_flag need to be int type

                index = 0
                while parts[0] + '[' + str(index) + parts[1] in self.all_keys['traces']['core_profiles']:
                    if tag.endswith('multiple_states_flag'):
                        traces[parts[0] + '[' + str(index) + parts[1]] = np.asarray([int(point) for point in traces[parts[0] + '[' + str(index) + parts[1]]])
                    else:
                        # Avoid transformation to np.str_
                        if type(traces[parts[0] + '[' + str(index) + parts[1]][0]) != str:
                            traces[parts[0] + '[' + str(index) + parts[1]] = np.asarray(traces[parts[0] + '[' + str(index) + parts[1]])
                    index += 1

    # ---------------------------- WORK IN PROGRESS -----------------------------
            elif len(parts) == 3:
                for profile in self.ids_struct[ids_iden].profiles_1d:
                    array1 = eval('profile.' + parts[0])
                    for index1, element1 in enumerate(array1):
                        array2 = eval('element1.' + parts[1][2:])
                        for index2, element2 in enumerate(array2):
                            point = eval('element2.' + parts[2][2:])
                            if parts[0] + '[' + str(index1) + parts[1]+ '[' + str(index2) + parts[2] not in self.all_keys['traces']['core_profiles']:
                                # Adding the keys
                                self.all_keys['traces']['core_profiles'].append(parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2])
                                traces[parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2]] = [point]
                            else:
                                traces[parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2]].append(point)

                index1 = 0
                while parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2] in self.all_keys['traces']['core_profiles']:
                    while parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2] in self.all_keys['traces']['core_profiles']:
                        if tag.endswith('atoms_n'):
                            traces[parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2]] = np.asarray([int(point) for point in traces[parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2]]])
                        else:
                            traces[parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2]] = np.asarray(traces[parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2]])
                        index2 += 1
                    index2 = 0
                    index1 += 1

    # -------------------------------------------------------------------------------
        time = self.ids_struct[ids_iden].time

        return profiles_1d, traces, time
    
    
    def extract_summary(self):
    
        traces = {}
        ids_iden = 'summary'
    
        for tag in keys_list['traces']['summary']:
            traces[tag] = eval('self.ids_struct[ids_iden].'+ tag)
    
        time = self.ids_struct[ids_iden].time

        # The n_e line averaged, at least for TCV, does not have data very early or very late. Will interpolate missing data.
        # Will assume that the density is not zero at the very beginning and very end. 0.5e19 is arbitrary...
        # This could be a single function

        if 'line_average.n_e.value' in traces:
            time_ne_average = time[np.where(np.isnan(traces['line_average.n_e.value']), False, True)]
            ne_average = traces['line_average.n_e.value'][np.where(np.isnan(traces['line_average.n_e.value']), False, True)]

            if np.size(traces['line_average.n_e.value']) != 0:
                traces['line_average.n_e.value'] = fit_and_substitute(time_ne_average, time, ne_average)

                if traces['line_average.n_e.value'][0] < 0:
                    time_ne_average.insert(0, time[0])
                    ne_average.insert(0, 0.5e19)

                if traces['line_average.n_e.value'][-1] < 0:
                    time_ne_average.append(time[-1])
                    ne_average.append(0.5e19)

                traces['line_average.n_e.value'] = fit_and_substitute(time_ne_average, time, ne_average)


        return traces, time
    
    
    def extract_equilibrium(self):
    
        profiles_2d, profiles_1d, traces, extras = {}, {}, {}, {}
        ids_iden = 'equilibrium'    

        for tag in keys_list['profiles_1d'][ids_iden]:
            parts = tag.split('[')
            # Initializing profiles
            if len(parts) == 1:
                profiles_1d[tag] = []
            elif len(parts) == 2:
    
                # A new list needs to be created, appending the keys including the values of the indexes of the nested elements
                self.all_keys['profiles_1d'][ids_iden].append(parts[0] + '[' + str(0) + parts[1])
                profiles_1d[parts[0] + '[' + str(0) + parts[1]] = []
    
            # Filling profiles
            for time_slice in self.ids_struct[ids_iden].time_slice:
                parts = tag.split('[')
                if len(parts) == 1:
                    point = eval('time_slice.' + tag)
                    profiles_1d[tag].append(point)
                elif len(parts) == 2:
                    point = eval('time_slice.' + parts[0] + '[' + str(0) + parts[1])
                    profiles_1d[parts[0] + '[' + str(0) + parts[1]].append(point)
    
        # Transforming to numpy arrays
        for key in profiles_1d:
            profiles_1d[key] = np.asarray(profiles_1d[key])
    
        # Filling traces

        # WORK IN PROGRESS -------------------------------

        for tag in keys_list['traces'][ids_iden]:
            parts = tag.split('[')
            if len(parts) == 1:
                traces[tag] = []
                for time_slice in self.ids_struct[ids_iden].time_slice:
                    point = eval('time_slice.' + tag)
                    traces[tag].append(point)

            if len(parts) == 2:
                for time_slice in self.ids_struct[ids_iden].time_slice:
                    array = eval('time_slice.' + parts[0])
                    for index, element in enumerate(array):
                        point = eval('element.' + parts[1][2:])
                        if parts[0] + '[' + str(index) + parts[1] not in traces:
                            self.all_keys['traces'][ids_iden].append(parts[0] + '[' + str(index) + parts[1])  # adding the key

                            traces[parts[0] + '[' + str(index) + parts[1]] = [point]
                        else:
                            traces[parts[0] + '[' + str(index) + parts[1]].append(point)

                # index needs to be an int
                index = 0
                while parts[0] + '[' + str(index) + parts[1] in self.all_keys['traces']['equilibrium']:
                    if tag.endswith('index'):
                        traces[parts[0] + '[' + str(index) + parts[1]] = np.asarray([int(point) for point in traces[parts[0] + '[' + str(index) + parts[1]]])
                    else:
                        # Avoid np.str_ type
                        if type(traces[parts[0] + '[' + str(index) + parts[1]][0]) != str:
                            traces[parts[0] + '[' + str(index) + parts[1]] = np.asarray(traces[parts[0] + '[' + str(index) + parts[1]])
                    index += 1


        # --------------------------------------------------


        # Transforming to numpy arrays. Not to be done when dealing with strings, imas does not recognize np.str_
        for key in traces:
            if type(traces[key][0]) != str:
                traces[key] = np.asarray(traces[key])
 
        for tag in keys_list['profiles_2d']['equilibrium']:
            parts = tag.split('[')
            # Initializing profiles
            if len(parts) == 1:
                profiles_2d[tag] = []
            elif len(parts) == 2:
                # A new list needs to be created, appending the keys including the values of the indexes of the nested elements
                self.all_keys['profiles_2d']['equilibrium'].append(parts[0] + '[' + str(0) + parts[1])
                profiles_2d[parts[0] + '[' + str(0) + parts[1]] = []

            for time_slice in self.ids_struct[ids_iden].time_slice:
                parts = tag.split('[')
                if len(parts) == 1:
                    point = eval('time_slice.' + tag)
                    profiles_2d[tag].append(point)
                elif len(parts) == 2:
                    point = eval('time_slice.' + parts[0] + '[' + str(0) + parts[1])
                    profiles_2d[parts[0] + '[' + str(0) + parts[1]].append(point)

        for key in profiles_2d:
            profiles_2d[key] = np.asarray(profiles_2d[key])

        time = self.ids_struct[ids_iden].time
    
        extras['b0'] = self.ids_struct[ids_iden].vacuum_toroidal_field.b0
        extras['r0'] = self.ids_struct[ids_iden].vacuum_toroidal_field.r0
    
        return profiles_2d, profiles_1d, traces, extras, time
    
    
    def extract_core_sources(self):
    
        profiles_1d, traces = {}, {}
        ids_iden = 'core_sources'
    
        for tag in keys_list['profiles_1d']['core_sources']:
            split = tag.split('#')
    
            if len(self.ids_struct[ids_iden].source) == 0:
                break
    
            i_source = get_index_source(split[0])
    
            parts = split[1].split('[')
    
            if len(parts) == 1:
                profiles_1d[tag] = []
            elif len(parts) == 2:
            # The new list is updated, appending the keys including the values of the indexes of the nested elements
                self.all_keys['profiles_1d']['core_sources'].append(parts[0] + '[' + str(0) + parts[1])
                profiles_1d[split[0] + '#' + parts[0] + '[' + str(0) + parts[1]] = []
    
            for profile in self.ids_struct[ids_iden].source[i_source].profiles_1d:
                if len(parts) == 1:
                    point = eval('profile.'+ split[1])
                    profiles_1d[split[0] + '#' + split[1]].append(point)
                elif len(parts) == 2:
                    point = eval('profile.' + parts[0] + '[' + str(0) + parts[1])
                    profiles_1d[split[0] + '#' + parts[0] + '[' + str(0) + parts[1]].append(point)
    
        for tag in keys_list['traces']['core_sources']:
            split = tag.split('#')
    
            if len(self.ids_struct[ids_iden].source) == 0:
                break
    
            i_source = get_index_source(split[0])
    
            parts = split[1].split('[')
    
             # How I would do it counting the number of tags and building the number of for loops accordingly
    
            if len(parts) == 1:
                traces[tag] = []
                for profile in self.ids_struct[ids_iden].source[i_source].profiles_1d:
                    point = eval('profile.' + tag)
                    self.ids_dicttraces[tag].append(point)
    
            if len(parts) == 2:
                for profile in self.ids_struct[ids_iden].source[i_source].profiles_1d:
                    array = eval('profile.' + parts[0])
                    for index, element in enumerate(array):
                        point = eval('element.' + parts[1][2:])
                        if not traces[split[0] + parts[0] + str(index) + parts[1]]:
                            self.all_keys['traces']['core_sources'].append(split[0] + '#' + parts[0] + '[' + str(index) + parts[1])  # adding the keys
                            traces[split[0] + '#' + parts[0] + '[' + str(index) + parts[1]] = [point]
                        else:
                            traces[split[0] + '#' + parts[0] + '[' + str(index) + parts[1]].append(point)
    
            if len(parts) == 3:
                for profile in self.ids_struct[ids_iden].source[2].profiles_1d:
                    array1 = eval('profile.' + parts[0])
                    for index1, element1 in enumerate(array1):
                        array2 = eval('element1.' + parts[1][2:])
                        for index2, element2 in enumerate(array2):
                            point = eval('element2.' + parts[2][2:])
                            if split[0] + '#' + parts[0] + '[' + str(index1) + parts[1] + str(index2) + '[' + parts[2] not in traces:
                                # Adding the keys
                                self.all_keys['traces']['core_sources'].append(split[0] + '#' + parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2])
                                traces[split[0] + '#' + parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2]] = [point]
                            else:
                                traces[split[0] + '#' + parts[0] + '[' + str(index1) + parts[1] + '[' + str(index2) + parts[2]].append(point)
    
        time = self.ids_struct[ids_iden].time
    
        return profiles_1d, traces, time
    
    
    #For now nbi works weird. Will fix later when I know how the nbi enters pencil
    def extract_nbi(self):
    
        profiles_1d, traces = {}, {}
        ids_iden = 'nbi' 
    
        parts = keys_list['traces']['nbi'][0].split('[')
        for index, unit in enumerate(self.ids_struct[ids_iden].unit):
            traces[parts[0] + '[' + str(index) + parts[1]] = eval('unit.' + parts[1][1:])
            self.all_keys['traces']['nbi'].append(parts[0] + '[' + str(index) + parts[1])
    
        parts = keys_list['profiles_1d']['nbi'][0].split('[')
        for index, unit in enumerate(self.ids_struct[ids_iden].unit):
            profiles_1d[parts[0] + '[' + str(index) + parts[1]] = eval('unit.' + parts[1][1:])
            self.all_keys['profiles_1d']['nbi'].append(parts[0] + '[' + str(index) + parts[1])
    
        time = self.ids_struct[ids_iden].time
    
        return profiles_1d, traces, time
    
    # ------------------------------------ MANIPULATION -------------------------------
    
    def select_interval(self, time_start, time_end):
        
        # Could be only one for loop
        for element_key in self.ids_dict['traces'].keys():
            for ids_key in ids_list:
                if element_key in self.all_keys['traces'][ids_key]:
                
                    time = self.ids_dict['time'][ids_key]
    
                    index_time_start = np.abs(time - time_start).argmin(0)
                    index_time_end = np.abs(time - time_end).argmin(0)
    
                    self.ids_dict['traces'][element_key] = self.ids_dict['traces'][element_key][index_time_start:index_time_end]
    
        for element_key in self.ids_dict['profiles_1d'].keys():
            for ids_key in ids_list:
                if element_key in self.all_keys['profiles_1d'][ids_key]:
    
                    time = self.ids_dict['time'][ids_key]
    
                    index_time_start = np.abs(time - time_start).argmin(0)
                    index_time_end = np.abs(time - time_end).argmin(0)
    
                    self.ids_dict['profiles_1d'][element_key] = self.ids_dict['profiles_1d'][element_key][index_time_start:index_time_end]

        for element_key in self.ids_dict['profiles_2d'].keys():
            # profiles 2d only availabe in equilibrium
            if element_key in self.all_keys['profiles_2d']['equilibrium']:

                time = self.ids_dict['time']['equilibrium']

                index_time_start = np.abs(time - time_start).argmin(0)
                index_time_end = np.abs(time - time_end).argmin(0)

                self.ids_dict['profiles_2d'][element_key] = self.ids_dict['profiles_2d'][element_key][index_time_start:index_time_end]

        # Also fill b0. Might want to change this in the future (but b0 in traces)
        time = self.ids_dict['time']['equilibrium']
        index_time_start = np.abs(time - time_start).argmin(0)
        index_time_end = np.abs(time - time_end).argmin(0)
        self.ids_dict['extras']['b0'] = self.ids_dict['extras']['b0'][index_time_start:index_time_end]

        for ids_key in ids_list:
            if ids_key in self.ids_dict['time'].keys():
                if len(self.ids_dict['time'][ids_key]) != 0:
                    time = self.ids_dict['time'][ids_key]
    
                    index_time_start = np.abs(time - time_start).argmin(0)
                    index_time_end = np.abs(time - time_end).argmin(0)
    
                    self.ids_dict['time'][ids_key] = self.ids_dict['time'][ids_key][index_time_start:index_time_end]
    
        self.fill_ids_struct()

    def average_traces_profile(self):
    
        for key in self.ids_dict['traces']:
            if len(self.ids_dict['traces'][key]) != 0:
                if type(self.ids_dict['traces'][key][0]) == str or type(self.ids_dict['traces'][key][0]) == np.str_:
                    # np.str_ is not recognized by imas. Signals are converted to str.
                    self.ids_dict['traces'][key] = [str(self.ids_dict['traces'][key][0])]
                elif type(self.ids_dict['traces'][key][0]) == int or type(self.ids_dict['traces'][key][0]) == np.int_:
                    self.ids_dict['traces'][key] = np.asarray([int(np.average(self.ids_dict['traces'][key]))])
                else:
                # The value is given in an array, helps having the same structure later when I will have to deal with more values
                    self.ids_dict['traces'][key] = np.asarray([np.average(self.ids_dict['traces'][key])])
            else:
                self.ids_dict['traces'][key] = np.asarray([])
    
        # averaging profiles
        for key in self.ids_dict['profiles_1d']:
            if len(self.ids_dict['profiles_1d'][key][0]) != 0:
                # Modified to eliminate infs. Might find a more elegant way to do it though
                self.ids_dict['profiles_1d'][key][self.ids_dict['profiles_1d'][key] == np.inf] = 0
                self.ids_dict['profiles_1d'][key][self.ids_dict['profiles_1d'][key] == -np.inf] = 0
    
                self.ids_dict['profiles_1d'][key] = np.average(np.transpose(np.asarray(self.ids_dict['profiles_1d'][key])), axis = 1)
                self.ids_dict['profiles_1d'][key] = np.reshape(self.ids_dict['profiles_1d'][key], (1,len(self.ids_dict['profiles_1d'][key])))
            else:
                self.ids_dict['profiles_1d'][key] = np.asarray([])

        # averaging 2d profiles
        for key in self.ids_dict['profiles_2d']:
            if len(self.ids_dict['profiles_2d'][key][0]) != 0:
                # Modified to eliminate infs. Might find a more elegant way to do it though
                self.ids_dict['profiles_2d'][key][self.ids_dict['profiles_2d'][key] == np.inf] = 0
                self.ids_dict['profiles_2d'][key][self.ids_dict['profiles_2d'][key] == -np.inf] = 0

                self.ids_dict['profiles_2d'][key] = np.average(self.ids_dict['profiles_2d'][key], axis = 0)
                self.ids_dict['profiles_2d'][key] = np.reshape(self.ids_dict['profiles_2d'][key], (1,np.shape(self.ids_dict['profiles_2d'][key])[0], np.shape(self.ids_dict['profiles_2d'][key])[1]))

            else:
                self.ids_dict['profiles_2d'][key] = np.asarray([])
    
        #Selecting the first time to be the place holder. Could also select the middle time
        for ids_key in ids_list:
            if ids_key in self.ids_dict['time'].keys():
                if len(self.ids_dict['time'][ids_key]) != 0:
                    self.ids_dict['time'][ids_key] = np.asarray([self.ids_dict['time'][ids_key][0]])
    
        self.ids_dict['extras']['b0'] = np.asarray([np.average(self.ids_dict['extras']['b0'])])
        self.fill_ids_struct()

    def update_times_traces(self, new_times, changing_idss):
    
        '''
    
        Changes the traces in a list of IDSs to a new time base
    
        '''

        for changing_ids in changing_idss:
            for key in self.ids_dict['traces'].keys():
                # It handles the interpolations for when strings are involved (the usecase I found is with labels)
                #if key in self.all_keys['traces'][changing_ids] and 'label' in key:
                if key in self.all_keys['traces'][changing_ids] and type(self.ids_dict['traces'][key][0]) == str:
                    self.ids_dict['traces'][key] = [str(a) for a in np.full(len(new_times), self.ids_dict['traces'][key][0])]

                # WORK IN PROGRESS

                elif key in self.all_keys['traces'][changing_ids] and type(self.ids_dict['traces'][key][0]) == np.int_:
                    self.ids_dict['traces'][key] = [int(a) for a in np.full(len(new_times), self.ids_dict['traces'][key][0])]


                elif key in self.all_keys['traces'][changing_ids] and len(self.ids_dict['traces'][key]) != 0:
                    self.ids_dict['traces'][key] = fit_and_substitute(self.ids_dict['time'][changing_ids], new_times, self.ids_dict['traces'][key])

        if 'equilibrium' in changing_idss:
            self.ids_dict['extras']['b0'] = fit_and_substitute(self.ids_dict['time']['equilibrium'], new_times, self.ids_dict['extras']['b0'])
    
    def update_times_profiles(self, new_times, changing_idss):
    
        # Rebasing the profiles in time
        for changing_ids in changing_idss:
            for key in self.ids_dict['profiles_1d'].keys():
                if key in self.all_keys['profiles_1d'][changing_ids] and len(self.ids_dict['profiles_1d'][key]) != 0:
    
                    old_times = self.ids_dict['time'][changing_ids]
                    # Getting the dimensions of the radial grid and time
                    x_dim = np.shape(self.ids_dict['profiles_1d'][key])[1]
                    time_dim = np.shape(self.ids_dict['profiles_1d'][key])[0]
                    profiles_new = {}
    
                    for i in np.arange(x_dim):
                        if key in profiles_new:
                            profiles_new[key] = np.hstack((profiles_new[key], fit_and_substitute(old_times, new_times, self.ids_dict['profiles_1d'][key][:,i])))
                        else:
                            profiles_new[key] = fit_and_substitute(old_times, new_times, self.ids_dict['profiles_1d'][key][:,i])
    
                    profiles_new[key] = profiles_new[key].reshape(x_dim, len(new_times))
                    self.ids_dict['profiles_1d'][key] = np.transpose(np.asarray(profiles_new[key]))
 
# WORK IN PROGRESS ----------------------------------------

    def update_times_2d_profiles(self, new_times, changing_idss):

        # Rebasing the profiles in time
        for changing_ids in changing_idss:
            for key in self.ids_dict['profiles_2d'].keys():
                if key in self.all_keys['profiles_2d'][changing_ids] and len(self.ids_dict['profiles_2d'][key]) != 0:

                    old_times = self.ids_dict['time'][changing_ids]
                    # Getting the dimensions of the radial grid and time
                    time_dim = np.shape(self.ids_dict['profiles_2d'][key])[0]
                    x_dim = np.shape(self.ids_dict['profiles_2d'][key])[1]
                    y_dim = np.shape(self.ids_dict['profiles_2d'][key])[2]
                    profiles_new = {}

                    for i in np.arange(x_dim):
                        for j in np.arange(y_dim):
                            if key in profiles_new:
                                profiles_new[key] = np.hstack((profiles_new[key], fit_and_substitute(old_times, new_times, self.ids_dict['profiles_2d'][key][:,i,j])))
                            else:
                                profiles_new[key] = fit_and_substitute(old_times, new_times, self.ids_dict['profiles_2d'][key][:,i,j])

                    profiles_new[key] = profiles_new[key].reshape(x_dim, y_dim, len(new_times))
                    self.ids_dict['profiles_2d'][key] = np.transpose(np.asarray(profiles_new[key]),[2,0,1])
# ---------------------------------------------------------------
   
    def update_times_times(self, new_times, changing_idss):
    
        for changing_ids in changing_idss:
            self.ids_dict['time'][changing_ids] = new_times
    
    def update_times(self, new_times, changing_idss):
    
        self.update_times_2d_profiles(new_times, changing_idss)
        self.update_times_profiles(new_times, changing_idss)
        self.update_times_traces(new_times, changing_idss)
        self.update_times_times(new_times, changing_idss)

        self.fill_ids_struct()
    
    def fill_ids_struct(self):

        # For summary r0 and b0 are to be filled with the old values.
        self.fill_summary()

        # --------------------- Fill core profiles -------------------------------
        self.fill_core_profiles()

        # --------------------- Fill equilibrium ---------------------------------
        self.fill_equilibrium()

        # --------------------- Fill core_sources --------------------------------
        self.fill_core_sources()

        # ------------------------- Filling nbi data -----------------------------
        #self.fill_nbi()

        # --------------------- Fill pulse scheduler --------------------------------
        self.fill_pulse_scheduler()



    # Might be cleaner to create a new self.ids_struct, but for how it is coded now it should not matter
    #return self.ids_struct

    def fill_basic_quantities(self, ids_iden):
    
        self.ids_struct[ids_iden] = eval('imas.' + ids_iden + '()')
    
        # Might want to specify this externally
        username=getpass.getuser()
    
        self.ids_struct[ids_iden].code.commit = 'unknown'
        self.ids_struct[ids_iden].code.name = 'Core_profiles_tools'
        self.ids_struct[ids_iden].code.output_flag = np.array([])
        self.ids_struct[ids_iden].code.repository = 'gateway'
        self.ids_struct[ids_iden].code.version = 'unknown'
    
        self.ids_struct[ids_iden].ids_properties.homogeneous_time = imasdef.IDS_TIME_MODE_HOMOGENEOUS
        self.ids_struct[ids_iden].ids_properties.provider = username
        self.ids_struct[ids_iden].ids_properties.creation_date = str(datetime.date)
        self.ids_struct[ids_iden].time = np.asarray([0.1])
    
    # Will need to think what to do here....  # THIS WILL BREAK THE CODE
    def fill_summary(self):
    
        ids_iden = 'summary'
        self.fill_basic_quantities(ids_iden)
   
        #self.ids_struct[ids_iden].global_quantities.r0.value = self.ids_struct_old[ids_iden].global_quantities.r0.value
        #self.ids_struct[ids_iden].global_quantities.b0.value = self.ids_struct_old[ids_iden].global_quantities.b0.value
    
        self.ids_struct[ids_iden].global_quantities.r0.value = self.ids_dict['extras']['r0']
        self.ids_struct[ids_iden].global_quantities.b0.value = self.ids_dict['extras']['b0']

        # Put the traces
        for tag in keys_list['traces']['summary']:
            rsetattr(self.ids_struct[ids_iden], tag, self.ids_dict['traces'][tag])
    
        self.ids_struct[ids_iden].time = self.ids_dict['time']['summary']
    
    #Need to adapt here to allow for multiple time slices
    
    def fill_core_profiles(self):
    
        ids_iden = 'core_profiles'
        self.fill_basic_quantities(ids_iden)
    
        profile_1d = imas.core_profiles().profiles_1d.getAoSElement()
        self.ids_struct[ids_iden].profiles_1d.append(profile_1d)
    
        # Put the profiles in the structure. A new element is created if it's not available
    
        for tag in keys_list['profiles_1d']['core_profiles']:
            if '[' not in tag:
                for index, profile_1d in enumerate(self.ids_dict['profiles_1d'][tag]):
                    if index >= np.shape(self.ids_struct[ids_iden].profiles_1d)[0]:
                        element = imas.core_profiles().profiles_1d.getAoSElement()
                        self.ids_struct[ids_iden].profiles_1d.append(element)
                    rsetattr(self.ids_struct[ids_iden].profiles_1d[index], tag, profile_1d)
            else:
                parts = tag.split('[')
    
                # put the profiles when there is one nested structure
                index2 = 0
                while parts[0] + '[' + str(index2) + parts[1] in self.ids_dict['profiles_1d'].keys():
                    for index1, profile_1d in enumerate(self.ids_dict['profiles_1d'][parts[0] + '[' + str(index2) + parts[1]]):
                        element = eval('self.ids_struct[ids_iden].profiles_1d[' + str(index1) + '].' + parts[0])
                        if index2 >= len(element):
                            new_profile = eval('self.ids_struct[ids_iden].profiles_1d[' + str(index1) + '].' + parts[0] + '.getAoSElement()')
                            eval('self.ids_struct[ids_iden].profiles_1d[' + str(index1) + '].' + parts[0] + '.append(new_profile)')
    
                        eval('rsetattr(self.ids_struct[ids_iden].profiles_1d[' + str(index1) + '].' + parts[0] + '[' + str(index2) + '], \'' + parts[1][2:] + '\', profile_1d)')
                    index2 += 1
    
    
        # Put the traces
        tag_type = 'traces'
    
        for tag in keys_list['traces']['core_profiles']:
            parts = tag.split('[')
            if(len(parts)) == 1:
                setattr(self.ids_struct[ids_iden].global_quantities, tag, self.ids_dict['traces'][tag])
    
    # ---------------------------- WORK IN PROGRESS -----------------------------
    
            elif(len(parts)) == 2:
                index2 = 0
                while parts[0] + '[' + str(index2) + parts[1] in self.ids_dict['traces'].keys():
                    for index1, trace in enumerate(self.ids_dict[tag_type][parts[0] + '[' + str(index2) + parts[1]]):
                        if index1 >= len(self.ids_struct[ids_iden].profiles_1d):
                            new_profile = self.ids_struct[ids_iden].profiles_1d.getAoSElement()
                            self.ids_struct[ids_iden].profiles_1d.append(new_profile)
                        #The addition of new elements might be generalized using eval
                        if index2 >= len(self.ids_struct[ids_iden].profiles_1d[index1].ion):
                            new_item = eval('self.ids_struct[ids_iden].profiles_1d[0].' + parts[0] + '.getAoSElement()')
                            self.ids_struct[ids_iden].profiles_1d[index1].ion.append(new_item)
                            #eval('self.ids_struct[ids_iden].profiles_1d[' + str(index1) + '].' + parts[0] + '.append(new_profile)')

                        eval('rsetattr(self.ids_struct[ids_iden].profiles_1d[' + str(index1) + '].' + parts[0] + '[' + str(index2) + '], \''
 + parts[1][2:] + '\', trace)')

                    index2 += 1

    # -------------------------------------------------------------------------------


            elif(len(parts)) == 3:
                index2 = 0
                while parts[0] + '[' + str(index2) + parts[1] + '[0' + parts[2] in self.ids_dict[tag_type].keys():
                    index3 = 0
                    while parts[0] + '[' + str(index2) + parts[1] + '[' + str(index3) + parts[2] in self.ids_dict[tag_type].keys():
                        for index1, profile_1d in enumerate(self.ids_dict[tag_type][parts[0] + '[' + str(index2) + parts[1] + '[' + str(index3) + parts[2]]):
                            if index1 >= len(self.ids_struct[ids_iden].profiles_1d):
                                new_profile = self.ids_struct[ids_iden].profiles_1d.getAoSElement()
                                self.ids_struct[ids_iden].profiles_1d.append(new_profile)
    
                            #The addition of new elements might be generalized using eval
                            if index2 >= len(self.ids_struct[ids_iden].profiles_1d[index1].ion):
                                new_item = eval('self.ids_struct[ids_iden].profiles_1d[0].' + parts[0] + '.getAoSElement()')
                                self.ids_struct[ids_iden].profiles_1d[index1].ion.append(new_item)
    
                            if index3 >= len(self.ids_struct[ids_iden].profiles_1d[index1].ion[index2].element):
                                new_item = eval('self.ids_struct[ids_iden].profiles_1d[0].' + parts[0] + '[0' + parts[1] + '.getAoSElement()')
                                self.ids_struct[ids_iden].profiles_1d[index1].ion[index2].element.append(new_item)
    
                            #for index1, profile_1d in enumerate(self.ids_dict[tag_type][split[0] + '#' + parts[0] + '[' + str(index2) + parts[1] + '[' + str(index3) + parts[2]]):
                            eval('rsetattr(self.ids_struct[ids_iden].profiles_1d[' + str(index1) + '].' + parts[0] + '[' + str(index2) + parts[1] + '[' + str(index3) + '] ,\'' + parts[2][2:] +'\', profile_1d)')
                        index3 += 1
                    index2 += 1

        self.ids_struct[ids_iden].time = self.ids_dict['time']['core_profiles']
    
    def fill_equilibrium(self):
    
        ids_iden = 'equilibrium'
        self.fill_basic_quantities(ids_iden)

# WORK IN PROGRESS --------------------------------------

        for tag in keys_list['profiles_2d']['equilibrium']:
            if '[' not in tag:
                for index, profile_2d in enumerate(self.ids_dict['profiles_2d'][tag]):
                    if index >= np.shape(self.ids_struct['equilibrium'].time_slice)[0]:
                        time_slice = imas.equilibrium().time_slice.getAoSElement()
                        self.ids_struct['equilibrium'].time_slice.append(time_slice)
                        profiles_2d = self.ids_struct['equilibrium'].time_slice[0].profiles_2d.getAoSElement()
                        self.ids_struct['equilibrium'].time_slice[index].profiles_2d.append(profiles_2d)
                    rsetattr(self.ids_struct['equilibrium'].time_slice[index], tag, profile_1d)
            else:
                parts = tag.split('[')

                # Put the profiles in the case of one nested structure
                index2 = 0
                while parts[0] + '[' + str(index2) + parts[1] in self.ids_dict['profiles_2d'].keys():
                    for index1, profile_2d in enumerate(self.ids_dict['profiles_2d'][parts[0] + '[' + str(index2) + parts[1]]):
                        if index1 >= np.shape(self.ids_struct['equilibrium'].time_slice)[0]:
                            time_slice = imas.equilibrium().time_slice.getAoSElement()
                            self.ids_struct['equilibrium'].time_slice.append(time_slice)
                            profiles_2d = self.ids_struct['equilibrium'].time_slice[0].profiles_2d.getAoSElement()
                            self.ids_struct['equilibrium'].time_slice[index1].profiles_2d.append(profiles_2d)

                        eval('rsetattr(self.ids_struct[\'equilibrium\'].time_slice[' + str(index1) + '].' + parts[0] + '[' + str(index2) + '], \'' + parts[1][2:] + '\', profile_2d)')
                    index2 += 1
#----------------------------------


        # Should append the time slice also for the splitted tags, to avoid ordering problems
        for tag in keys_list['profiles_1d']['equilibrium']:
            if '[' not in tag:
                for index, profile_1d in enumerate(self.ids_dict['profiles_1d'][tag]):
                    if index >= np.shape(self.ids_struct[ids_iden].time_slice)[0]:
                        time_slice = imas.equilibrium().time_slice.getAoSElement()
                        self.ids_struct[ids_iden].time_slice.append(time_slice)
                        profiles_2d = self.ids_struct[ids_iden].time_slice[0].profiles_2d.getAoSElement()
                        self.ids_struct[ids_iden].time_slice[index].profiles_2d.append(profiles_2d)
                    rsetattr(self.ids_struct[ids_iden].time_slice[index], tag, profile_1d)
            else:
                parts = tag.split('[')
    
                # Put the profiles in the case of one nested structure
                index2 = 0
                while parts[0] + '[' + str(index2) + parts[1] in self.ids_dict['profiles_1d'].keys():
                    for index1, profile_1d in enumerate(self.ids_dict['profiles_1d'][parts[0] + '[' + str(index2) + parts[1]]):
                        eval('rsetattr(self.ids_struct[ids_iden].time_slice[' + str(index1) + '].' + parts[0] + '[' + str(index2) + '], \'' + parts[1][2:] + '\', profile_1d)')
                    index2 += 1
    
        tag_type = 'traces'

        for tag in keys_list['traces'][ids_iden]:
            if '[' not in tag:
                for index, trace in enumerate(self.ids_dict['traces'][tag]):
                    if index >= np.shape(self.ids_struct[ids_iden].time_slice)[0]:
                        time_slice = imas.equilibrium().time_slice.getAoSElement()
                        self.ids_struct[ids_iden].time_slice.append(time_slice)
                        profiles_2d = self.ids_struct[ids_iden].time_slice[0].profiles_2d.getAoSElement()
                        self.ids_struct[ids_iden].time_slice[0].profiles_2d.append(profiles_2d)
    
                    rsetattr(self.ids_struct[ids_iden].time_slice[index], tag, trace)

# WORK IN PROGRESS --------------------------------------------------------
            else:
                parts = tag.split('[')
                index2 = 0
                while parts[0] + '[' + str(index2) + parts[1] in self.ids_dict['traces'].keys():
                    for index1, trace in enumerate(self.ids_dict[tag_type][parts[0] + '[' + str(index2) + parts[1]]):
                        if index1 >= len(self.ids_struct[ids_iden].time_slice):
                            new_slice = self.ids_struct[ids_iden].time_slice.getAoSElement()
                            self.ids_struct[ids_iden].time_slice.append(new_slice)
                        #The addition of new elements might be generalized using eval
                        if index2 >= len(self.ids_struct[ids_iden].time_slice[index1].profiles_2d):
                            new_item = eval('self.ids_struct[ids_iden].time_slice[0].' + parts[0] + '.getAoSElement()')
                            self.ids_struct[ids_iden].time_slice[index1].profiles_2d.append(new_item)
                            #eval('self.ids_struct[ids_iden].profiles_1d[' + str(index1) + '].' + parts[0] + '.append(new_profile)')

                        eval('rsetattr(self.ids_struct[ids_iden].time_slice[' + str(index1) + '].' + parts[0] + '[' + str(index2) + '], \''
 + parts[1][2:] + '\', trace)')

                    index2 += 1

# ---------------------------------------------------------------------------


        # These are not in time_slice, so need to be treated separately
    
        self.ids_struct[ids_iden].vacuum_toroidal_field.b0 = self.ids_dict['extras']['b0']
        self.ids_struct[ids_iden].vacuum_toroidal_field.r0 = self.ids_dict['extras']['r0']
    
        self.ids_struct[ids_iden].time = self.ids_dict['time']['equilibrium']
    
    def get_index_source(self, split):
    
        if split == 'total':
            i_source = 0
    
        if split == 'nbi':
            i_source = 1
    
        if split == 'ec':
            i_source = 2
    
        if split == 'lh':
            i_source = 3
    
        if split == 'ic':
            i_source = 4
    
        return(i_source)
    
    def fill_core_sources(self):
    
        ids_iden = 'core_sources'
        self.fill_basic_quantities(ids_iden)

        # Should be possible to generalize here so this piece of code works for all the cases
    
        for tag_type in ['profiles_1d', 'traces']:
            for tag in keys_list[tag_type]['core_sources']:
                # Maybe not the ideal way to do it? It will probably break if there are only one or a few sources.
    
                # Only fills the tags actually in the dictionary
                if tag not in self.ids_dict[tag_type]:
                    break
    
                split = tag.split('#')
                i_source = get_index_source(split[0])
    
                parts = split[1].split('[')
                if len(parts) == 1:
    
                    while len(self.ids_struct[ids_iden].source) <= i_source:
                        new_source = self.ids_struct[ids_iden].source.getAoSElement()
                        self.ids_struct[ids_iden].source.append(new_source)
    
                    for index, profile_1d in enumerate(self.ids_dict[tag_type][tag]):
                        if index >= len(self.ids_struct[ids_iden].source[i_source].profiles_1d):
                            new_profile = self.ids_struct[ids_iden].source[i_source].profiles_1d.getAoSElement()
                            self.ids_struct[ids_iden].source[i_source].profiles_1d.append(new_profile)
                        rsetattr(self.ids_struct[ids_iden].source[i_source].profiles_1d[index], split[1], profile_1d)
    
                elif len(parts) == 2:
                    index2 = 0
                    while split[0] + '#' + parts[0] + '[' + str(index2) + parts[1] in self.ids_dict[tag_type].keys():
                        for index1, profile_1d in enumerate(self.ids_dict[tag_type][split[0] + '#' + parts[0] + '[' + str(index2) + parts[1]]):
                            # Inserts the correct structures in the new ids if the don't exist for a given index
                            if index1 >= len(self.ids_struct[ids_iden].source[i_source].profiles_1d):
                                new_profile = self.ids_struct[ids_iden].source[i_source].profiles_1d.getAoSElement()
                                self.ids_struct[ids_iden].source[i_source].profiles_1d.append(new_profile)
    
                            if index2 >= len(self.ids_struct[ids_iden].source[i_source].profiles_1d[index1].ion):
                                new_item = eval('self.ids_struct[ids_iden].source[i_source].profiles_1d[0].' + parts[0] + '.getAoSElement()')
                                self.ids_struct[ids_iden].source[i_source].profiles_1d[index1].ion.append(new_item)
    
                            eval('rsetattr(self.ids_struct[ids_iden].source[' + str(i_source) + '].profiles_1d[' + str(index1) + '].' + parts[0] + '[' + str(index2) + '] ,\'' + parts[1][3:] +'\', profile_1d)')
                        index2 += 1
    
            
                elif(len(parts)) == 3:
                    index2 = 0
                    while split[0] + '#' + parts[0] + '[' + str(index2) + parts[1] + '[0' + parts[2] in self.ids_dict[tag_type].keys():
                        index3 = 0
                        while split[0] + '#' + parts[0] + '[' + str(index2) + parts[1] + '[' + str(index3) + parts[2] in self.ids_dict[tag_type].keys():
                            for index1, profile_1d in enumerate(self.ids_dict[tag_type][split[0] + '#' + parts[0] + '[' + str(index2) + parts[1] + '[' + str(index3) + parts[2]]):
                                if index1 >= len(self.ids_struct[ids_iden].source[i_source].profiles_1d):
                                    new_profile = self.ids_struct[ids_iden].source[i_source].profiles_1d.getAoSElement()
                                    self.ids_struct[ids_iden].source[i_source].profiles_1d.append(new_profile)
    
                                #The addition of new elements might be generalized using eval
                                if index2 >= len(self.ids_struct[ids_iden].source[i_source].profiles_1d[index1].ion):
                                    new_item = eval('self.ids_struct[ids_iden].source[i_source].profiles_1d[0].' + parts[0] + '.getAoSElement()')
                                    self.ids_struct[ids_iden].source[i_source].profiles_1d[index1].ion.append(new_item)
    
                                if index3 >= len(self.ids_struct[ids_iden].source[i_source].profiles_1d[index1].ion[index2].element):
                                    new_item = eval('self.ids_struct[ids_iden].source[i_source].profiles_1d[0].' + parts[0] + '[0' + parts[1] + '.getAoSElement()')
                                    self.ids_struct[ids_iden].source[i_source].profiles_1d[index1].ion[index2].element.append(new_item)
    
                                    #for index1, profile_1d in enumerate(self.ids_dict[tag_type][split[0] + '#' + parts[0] + '[' + str(index2) + parts[1] + '[' + str(index3) + parts[2]]):
                                eval('rsetattr(self.ids_struct[ids_iden].source[' + str(i_source) + '].profiles_1d[' + str(index1) + '].' + parts[0] + '[' + str(index2) + parts[1] + '[' + str(index3) + '] ,\'' + parts[2][2:] +'\', profile_1d)')
    
                            index3 += 1
                        index2 += 1
    
        self.ids_struct[ids_iden].time = self.ids_dict['time']['core_sources']
    
    # nbi does not have a lot of time dependent fields so the structure is a little different. The old IDS is copied and not rebuilt from scratch
    
    def fill_nbi(self):
    
        ids_iden = 'nbi'

        parts = keys_list['traces']['nbi'][0].split('[')
        index = 0
        while parts[0] + '[' + str(index) + parts[1] in self.ids_dict['traces'].keys():
            eval('rsetattr(self.ids_struct[ids_iden][\'nbi\'].unit[' + str(index) + parts[1] + '] ,\'' + parts[1] + '\', self.ids_dict_new[\'traces\'][\'parts[0] + \'[\' + str(index) + parts[1]\'])')
            index += 1
    
        parts = keys_list['profiles_1d']['nbi'][0].split('[')
        index = 0
        while parts[0] + '[' + str(index) + parts[1] in self.ids_dict['profiles_1d'].keys():
            eval('rsetattr(self.ids_struct[ids_iden][\'nbi\'].unit[' + str(index) + parts[1] + '] ,\'' + parts[1] + '\', self.ids_dict_new[\'profiles_1d\'][\'parts[0] + \'[\' + str(index) + parts[1]\'])')
            index += 1

    def fill_pulse_scheduler(self):

        ids_iden = 'pulse_schedule'
        self.fill_basic_quantities(ids_iden)

        # And then interpolate all traces to the pulse_schedule.time time schedule

        self.ids_struct[ids_iden].time = self.ids_dict['time']['core_profiles']

        if 'b0' in self.ids_dict['extras']:
            if len(self.ids_dict['extras']['b0']) != 1:
            # Might still be needed becouse of bugs and the flipping ip
                self.ids_struct[ids_iden].tf.b_field_tor_vacuum_r.reference.data = fit_and_substitute(self.ids_dict['time']['equilibrium'], self.ids_struct[ids_iden].time, self.ids_dict['extras']['r0']*self.ids_dict['extras']['b0'])
                #self.ids_struct[ids_iden].tf.b_field_tor_vacuum_r.reference.data = np.abs(fit_and_substitute(self.ids_dict['time']['equilibrium'], self.ids_struct[ids_iden].time, self.ids_dict['extras']['r0']*self.ids_dict['extras']['b0']))
            else:
                #self.ids_struct[ids_iden].tf.b_field_tor_vacuum_r.reference.data = np.abs(self.ids_dict['extras']['r0']*self.ids_dict['extras']['b0'])
                self.ids_struct[ids_iden].tf.b_field_tor_vacuum_r.reference.data = self.ids_dict['extras']['r0']*self.ids_dict['extras']['b0']
            self.ids_struct[ids_iden].tf.b_field_tor_vacuum_r.reference.time = self.ids_dict['time']['core_profiles']

        if len(self.ids_dict['traces']['global_quantities.ip']) !=0:
            if len(self.ids_dict['traces']['global_quantities.ip']) != 1:
                self.ids_struct[ids_iden].flux_control.i_plasma.reference.data = fit_and_substitute(self.ids_dict['time']['equilibrium'], self.ids_struct[ids_iden].time, self.ids_dict['traces']['global_quantities.ip'])
            else:
                self.ids_struct[ids_iden].flux_control.i_plasma.reference.data = self.ids_dict['traces']['global_quantities.ip']
            self.ids_struct[ids_iden].flux_control.i_plasma.reference.time = self.ids_dict['time']['core_profiles']


        if len(self.ids_dict['traces']['line_average.n_e.value']) !=0:
            if len(self.ids_dict['traces']['line_average.n_e.value']) != 1:
                self.ids_struct[ids_iden].density_control.n_e_line.reference.data = fit_and_substitute(self.ids_dict['time']['summary'], self.ids_struct[ids_iden].time, self.ids_dict['traces']['line_average.n_e.value'])
            else:
                self.ids_struct[ids_iden].density_control.n_e_line.reference.data = self.ids_dict['traces']['line_average.n_e.value']
            self.ids_struct[ids_iden].density_control.n_e_line.reference.time = self.ids_dict['time']['core_profiles']


        #fit_and_substitute(old_times, new_times, self.ids_dict['profiles_1d'][key][:,i])

        # Heating, not available yet

        #pulse_schedule.nbi.unit[iunit].power.reference.time
        #pulse_schedule.nbi.unit[iunit].power.reference.data

        #pulse_schedule.ec.launcher[iloop].power.reference.time
        #pulse_schedule.ec.launcher[iloop].power.reference.data

        #pulse_schedule.ec.launcher[iloop].steering_angle_pol.reference.time
        #pulse_schedule.ec.launcher[iloop].steering_angle_pol.reference.data

        #pulse_schedule.ec.launcher[iloop].steering_angle_tor.reference.time
        #pulse_schedule.ec.launcher[iloop].steering_angle_tor.reference.data

        #pulse_schedule.lh.antenna[iloop].power.reference.time
        #pulse_schedule.lh.antenna[iloop].power.reference.data

        #pulse_schedule.ic.antenna[iloop].power.reference.time
        #pulse_schedule.ic.antenna[iloop].power.reference.data


# -------------------------------------------- MANIPULATE IDSS -----------------------------------------------



def select_interval_ids(db, shot, run, run_target, time_start, time_end, username = None):

    if not username:
        username = getpass.getuser()

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_data.select_interval(time_start, time_end)

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

def average_integrated_modelling(db, shot, run, run_target, time_start, time_end, username = None):

    '''

    Average all the fields in integrated modelling that are useful for the integrated modelling and saves a new ids with just the averages

    '''
    if not username:
        username = getpass.getuser()

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_data.select_interval(time_start, time_end)
    ids_data.average_traces_profile()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

def rebase_integrated_modelling(db, shot, run, run_target, new_times, changing_idss, username = None):

    '''

    Fits the ids on a new time base and creates a new ids. 'changing_idss' contains the names of the idss that will be rebased in time

    '''

    if not username:
        username = getpass.getuser()

    core_profiles = open_and_get_core_profiles(db, shot, run)

    ids_data = IntegratedModellingDict(db, shot, run, username = username)    
    ids_data.update_times(new_times, changing_idss)

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

def smooth_t_and_d_ids_new(db, shot, run, db_target, shot_target, run_target, username = '', username_target = ''):

    '''

    Inserts one more slice for every slice. All the values in new slices are interpolated. A new IDS is created

    '''

    if username == '': username = getpass.getuser()

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    new_times = double_time(core_profiles.time)
    ids_data.update_times(new_times, changing_idss)

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)


# Might want to move this guys in another file with other small functions that I use here and there
def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)

def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))


# ----------------------------- FILL PULSE SCHEDULER IDS  ---------------------------------

# ------------------------- EXTRA TOOLS TO OPEN AND PUT IDSS ------------------------------


def open_integrated_modelling(db, shot, run, username='', backend='mdsplus'):

    '''

    Opens the idss useful for integrated modelling and saves the fields in a conveniently to use dictionary. This should be done with IMASpy when I learn how to do it.
    Might also just save everything and then check and sort the dimensions later

    '''

    imas_backend = imasdef.MDSPLUS_BACKEND
    if backend == 'hdf5':
        imas_backend = imasdef.HDF5_BACKEND

    if username == '':
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=username)

    op = data_entry.open()

    ids_struct = {}
    #ids_list = ['core_profiles', 'core_sources', 'ec_launchers', 'equilibrium', 'nbi', 'summary', 'thomson_scattering']
    ids_list = ['core_profiles', 'core_sources', 'equilibrium', 'nbi', 'summary', 'thomson_scattering']

    for ids in ids_list:
        ids_struct[ids] = data_entry.get(ids)

    data_entry.close()

    return(ids_struct)

def open_and_get_core_profiles(db, shot, run, username='', backend='mdsplus'):

    imas_backend = imasdef.MDSPLUS_BACKEND
    if backend == 'hdf5':
        imas_backend = imasdef.HDF5_BACKEND

    if username == '':
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=username)

    op = data_entry.open()

    if op[0]<0:
        cp=data_entry.create()
        print(cp[0])
        if cp[0]==0:
            print("data entry created")
    elif op[0]==0:
        print("data entry opened")

    core_profiles = data_entry.get('core_profiles')
    data_entry.close()

    return(core_profiles)


def open_and_get_equilibrium(db, shot, run, username='', backend='mdsplus'):

    imas_backend = imasdef.MDSPLUS_BACKEND
    if backend == 'hdf5':
        imas_backend = imasdef.HDF5_BACKEND

    if username == '':
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=username)

    op = data_entry.open()

    if op[0]<0:
        cp=data_entry.create()
        print(cp[0])
        if cp[0]==0:
            print("data entry created")
    elif op[0]==0:
        print("data entry opened")

    equilibrium = data_entry.get('equilibrium')
    data_entry.close()

    return(equilibrium)

#Redundant since I can just use partial get

def open_and_get_equilibrium_tag(db, shot, run, tag, username='', backend='mdsplus', prefix='global_quantities'):

    imas_backend = imasdef.MDSPLUS_BACKEND
    if backend == 'hdf5':
        imas_backend = imasdef.HDF5_BACKEND

    if username == '':
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=username)

    op = data_entry.open()

    if op[0]<0:
        cp=data_entry.create()
        print(cp[0])
        if cp[0]==0:
            print("data entry created")
    elif op[0]==0:
        print("data entry opened")

    time = data_entry.partial_get('equilibrium', 'time(:)')
    variable = data_entry.partial_get('equilibrium', 'time_slice(:)/' + prefix + '/' + tag)
    data_entry.close()

    return(time, variable)

def open_and_get_summary(db, shot, run, username=None, backend='mdsplus'):

    imas_backend = imasdef.MDSPLUS_BACKEND
    if backend == 'hdf5':
        imas_backend = imasdef.HDF5_BACKEND

    if not isinstance(username, str):
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=username)

    op = data_entry.open()

    if op[0]<0:
        cp=data_entry.create()
        print(cp[0])
        if cp[0]==0:
            print("data entry created")
    elif op[0]==0:
        print("data entry opened")

    summary = data_entry.get('summary')
    data_entry.close()

    return(summary)

def open_and_get_core_sources(db, shot, run, username='', backend='mdsplus'):

    imas_backend = imasdef.MDSPLUS_BACKEND
    if backend == 'hdf5':
        imas_backend = imasdef.HDF5_BACKEND

    if username == '':
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=username)

    op = data_entry.open()

    if op[0]<0:
        cp=data_entry.create()
        print(cp[0])
        if cp[0]==0:
            print("data entry created")
    elif op[0]==0:
        print("data entry opened")

    core_sources = data_entry.get('core_sources')
    data_entry.close()

    return(core_sources)


def open_and_get_nbi(db, shot, run, username='', backend='mdsplus'):

    imas_backend = imasdef.MDSPLUS_BACKEND
    if backend == 'hdf5':
        imas_backend = imasdef.HDF5_BACKEND

    if username == '':
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=username)

    op = data_entry.open()

    if op[0]<0:
        cp=data_entry.create()
        print(cp[0])
        if cp[0]==0:
            print("data entry created")
    elif op[0]==0:
        print("data entry opened")

    nbi = data_entry.get('nbi')
    data_entry.close()

    return(nbi)

def open_and_get_all(db, shot, run, username='', backend='mdsplus'):

    '''

    Opens all the idss create for TCV. This should be done with IMASpy when I learn how to do it.

    '''

    imas_backend = imasdef.MDSPLUS_BACKEND
    if backend == 'hdf5':
        imas_backend = imasdef.HDF5_BACKEND

    if username == '':
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imas_backend, db, shot, run, user_name=username)

    op = data_entry.open()

    ids_dict = {}
    ids_list = ['core_profiles', 'core_sources', 'core_transport', 'ec_launchers', 'equilibrium', 'nbi', 'pf_active', 'summary', 'thomson_scattering', 'tf', 'wall']

    for ids in ids_list:
        ids_dict['ids'] = data_entry.get(ids)

    data_entry.close()

    return(ids_dict)

def put_integrated_modelling(db, shot, run, run_target, ids_struct, backend='mdsplus'):

    '''

    Puts the IDSs useful for integrated modelling. This should be done with IMASpy when I learn how to do it.

    '''

    imas_backend = imasdef.MDSPLUS_BACKEND
    if backend == 'hdf5':
        imas_backend = imasdef.HDF5_BACKEND

    username = getpass.getuser()
    copy_ids_entry(username, db, shot, run, shot, run_target)

    data_entry = imas.DBEntry(imas_backend, db, shot, run_target, user_name=getpass.getuser())
    ids_list = ['core_profiles', 'core_sources', 'ec_launchers', 'equilibrium', 'nbi', 'summary', 'thomson_scattering', 'pulse_schedule']

    op = data_entry.open()

    for ids in ids_list:
    # If the time vector is empty the IDS is empty or broken, do not put
        if len(ids_struct[ids].time) !=0:
            data_entry.put(ids_struct[ids])

    data_entry.close()


# ------------------------- EXTRA TOOLS TO MODIFY IDSS ------------------------------

# ------------------------------- ZEFF MANIPULATION ---------------------------------

# Name changed. Need to change it in prepare input
def set_flat_Zeff(db, shot, run, run_target, option, username = ''):

    '''

    Writes a new ids with a flat Zeff.

    '''
    if username == '':
        username = getpass.getuser()

    core_profiles = open_and_get_core_profiles(db, shot, run, username)
    Zeff = np.array([])

    for profile_1d in core_profiles.profiles_1d:
        Zeff = np.hstack((Zeff, profile_1d.zeff))

    len_time = len(core_profiles.time)
    len_x = len(core_profiles.profiles_1d[0].zeff)

    Zeff.reshape(len_time, len_x)

#    len_time, len_x = np.shape(Zeff)[0], np.shape(Zeff)[1]
    max_Zeff, min_zeff = np.max(Zeff), np.min(Zeff)

    if option == 'maximum':
        # The maximum Zeff might be too large, the not completely ionized carbon close to the LCFS might lead to a negative main ion density.
        # Reducing the value in this case.
        if max_Zeff < 4.5:
            Zeff_value = max_Zeff
        else:
            Zeff_value = 4.5

    elif option == 'minimum':
        if min_zeff > 1.02:
            Zeff_value = min_zeff
        else:
            Zeff_value = 1.02
    elif option == 'median':
        if max_Zeff < 4.5:
            Zeff_value = (max_Zeff + min_zeff)/2
        else:
            Zeff_value = (4.5 + min_zeff)/2

    else:
        print('Option not recognized, aborting. This should not happen')
        exit()

    Zeff = np.full((len_time, len_x), Zeff_value)

    for index, zeff_slice in enumerate(Zeff):
        core_profiles.profiles_1d[index].zeff = zeff_slice

    copy_ids_entry(username, db, shot, run, shot, run_target)

    data_entry_target = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run_target, user_name=username)

    op = data_entry_target.open()
    core_profiles.put(db_entry = data_entry_target)
    data_entry_target.close()

def correct_zeff(db, shot, run, db_target, shot_target, run_target, username = '', username_target = ''):

    '''

    Sets Zeff = 1.02 where Zeff falls below 1 for whatever reason (can happen if experimental data is taken automatically and not properly checked). Also, values greater than
4.5 are clumped (to avoid negative main ion density). The choice of 4.5 can be improved, itś made under the hypotesis that the impurity is carbon. Higher than this and it migh
t die close to the boundaries.
    Uses new_classes to do it

    '''

    if username == '':
        username=getpass.getuser()

    ids_data = IntegratedModellingDict(db, shot, run, username = username)

    ids_dict = ids_data.ids_dict

    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] > 1, ids_dict['profiles_1d']['zeff'], 1.02)
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] < 4.5, ids_dict['profiles_1d']['zeff'], 4.5)

    # Put the data back in the ids structure

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

    print('zeff corrected')

# WORK IN PROGRESS

def set_parabolic_zeff(db, shot, run, run_target, zeff_mult = 1, db_target = None, shot_target = None, username = None, username_target = None):

    '''

    Sets a parabolic Zeff profile

    '''

    if not username:
        username=getpass.getuser()
    if not db_target:
        db_target = db
    if not shot_target:
        shot_target = shot
    if not username_target:
        username_target = username

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] > 1, ids_dict['profiles_1d']['zeff'], 1.02)
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] < 4.5, ids_dict['profiles_1d']['zeff'], 4.5)

    average_zeff = []

    for profile in ids_dict['profiles_1d']['zeff']:
        average_zeff.append(np.average(profile))

    for index in range(np.shape(ids_dict['profiles_1d']['zeff'])[0]):
        norm = zeff_mult * (average_zeff[index]-1)/2
        ids_dict['profiles_1d']['zeff'][index] = average_zeff[index] + norm/2 - norm * np.sqrt(1-ids_dict['profiles_1d']['grid.rho_tor_norm'][index])

    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] > 1, ids_dict['profiles_1d']['zeff'], 1.02)
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] < 4.5, ids_dict['profiles_1d']['zeff'], 4.5)

    # Put the data back in the ids structure

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

    print('zeff turned parabolic')

def set_peaked_zeff_profile(db, shot, run, run_target, db_target = None, shot_target = None, username = None, username_target = None, verbose = False, zeff_mult = 1):

    if not username:
        username=getpass.getuser()
    if not db_target:
        db_target = db
    if not shot_target:
        shot_target = shot
    if not username_target:
        username_target = username

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict


    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] > 1, ids_dict['profiles_1d']['zeff'], 1.02)
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] < 5, ids_dict['profiles_1d']['zeff'], 5)

    average_zeff = []

    for profile in ids_dict['profiles_1d']['zeff']:
        average_zeff.append(np.average(profile))

    for index in range(np.shape(ids_dict['profiles_1d']['zeff'])[0]):
        norm = zeff_mult * (average_zeff[index]-1)/2
        ids_dict['profiles_1d']['zeff'][index] = average_zeff[index] - norm/2 + norm * np.sqrt(1-ids_dict['profiles_1d']['grid.rho_tor_norm'][index])

    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] > 1, ids_dict['profiles_1d']['zeff'], 1.02)
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] < 5, ids_dict['profiles_1d']['zeff'], 5)

    # Put the data back in the ids structure

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)


def set_hyperbole_zeff(db, shot, run, run_target, db_target = None, shot_target = None, username = None, username_target = None, verbose = False):

    if not username:
        username=getpass.getuser()
    if not db_target:
        db_target = db
    if not shot_target:
        shot_target = shot
    if not username_target:
        username_target = username

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    time_eq = ids_dict['time']['equilibrium']
    ip = ids_dict['traces']['global_quantities.ip']

    # The steady state is identified
    index_start_ft, index_end_ft = identify_flattop_ip(ip, time_eq)

    # Coef1 is calculated for Zeff to be continuous when the ramp up ends
    zeff_target, time_target = ids_dict['profiles_1d']['zeff'][index_start_ft][0], time_eq[index_start_ft]

    # c is the parameter controlling how fast zeff descents after the beginning. Z0 is zeff at t=0
    z0 = 4
    c = 10
    #b = (zeff_target - z0)/(-1 + 1/((c*time_target)**2 +1))
    b = (zeff_target-z0)/(-1+1/((c*time_target)**4+1))
    a = -b + z0

    time = ids_dict['time']['core_profiles']

    # Only changed at the beginning. Not adequate for ramp down. For that I would need to identify the last flattop, currently not done.
    zeff_new, index = [], 0
    for z in ids_dict['profiles_1d']['zeff'][:index_start_ft]:
        zeff_new.append(np.full((np.size(z)), a + b/((c*time[index])**4 +1)))
        index += 1

    for z in ids_dict['profiles_1d']['zeff'][index_start_ft:]:
        zeff_new.append(ids_dict['profiles_1d']['zeff'][index])
        index += 1

    ids_dict['profiles_1d']['zeff'] = np.asarray(zeff_new)

    #4 should be fine as a limit for Zeff. Lower than usual due to possible lower temperature at the beginning
    # Especially when combined with add profiles early
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] > 1, ids_dict['profiles_1d']['zeff'], 1.02)
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] < 4.0, ids_dict['profiles_1d']['zeff'], 4.0)

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)



def set_ip_ne_scaled_zeff(db, shot, run, run_target, db_target = None, shot_target = None, username = None, username_target = None, verbose = False):

    if not username:
        username=getpass.getuser()
    if not db_target:
        db_target = db
    if not shot_target:
        shot_target = shot
    if not username_target:
        username_target = username

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    ip = ids_dict['traces']['global_quantities.ip']
    ne = np.average(ids_dict['profiles_1d']['electrons.density'], axis = 1)
    time = ids_dict['time']['equilibrium']


    # The steady state is identified
    index_start_ft, index_end_ft = identify_flattop_ip(ip, time)

    # Coef1 is calculated for Zeff to be continuous when the ramp up ends
    zeff_target = ids_dict['profiles_1d']['zeff'][index_start_ft][0]
    ip_target, ne_target = ip[index_start_ft], ne[index_start_ft]

    coef2 = 3
    coef1 = (zeff_target - 1)/(ip_target/ne_target)**coef2

    # Only changed at the beginning. Not adequate for ramp down. For that I would need to identify the last flattop, currently not done.
    zeff_new, index = [], 0
    for z in ids_dict['profiles_1d']['zeff'][:index_start_ft]:
        zeff_new.append(np.full((np.size(z)), 1 + coef1*(ip[index]/ne[index])**coef2))
        index += 1

    for z in ids_dict['profiles_1d']['zeff'][index_start_ft:]:
        zeff_new.append(ids_dict['profiles_1d']['zeff'][index])
        index += 1

    ids_dict['profiles_1d']['zeff'] = np.asarray(zeff_new)

    #4 should be fine as a limit for Zeff. Lower than usual due to possible lower temperature at the beginning
    # Especially when combined with add profiles early
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] > 1, ids_dict['profiles_1d']['zeff'], 1.02)
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] < 4.0, ids_dict['profiles_1d']['zeff'], 4.0)

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)


def set_linear_descending_zeff(db, shot, run, run_target, db_target = None, shot_target = None, username = None, username_target = None, verbose = False):

    if not username:
        username=getpass.getuser()
    if not db_target:
        db_target = db
    if not shot_target:
        shot_target = shot
    if not username_target:
        username_target = username

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    ip = ids_dict['traces']['global_quantities.ip']
    time = ids_dict['time']['equilibrium']

    # The steady state is identified
    index_start_ft, index_end_ft = identify_flattop_ip(ip, time)

    zeff_target = ids_dict['profiles_1d']['zeff'][index_start_ft][0]

    # Only changed at the beginning. Not adequate for ramp down. For that I would need to identify the last flattop, currently not done.
    zeff_new = []
    for index, z in enumerate(ids_dict['profiles_1d']['zeff'][:index_start_ft]):
        zeff_new.append(np.full((np.size(z)), -4/time[index_start_ft]*time[index] + 4))

    for index, z in enumerate(ids_dict['profiles_1d']['zeff'][index_start_ft:]):
        zeff_new.append(ids_dict['profiles_1d']['zeff'][index])


    ids_dict['profiles_1d']['zeff'] = np.asarray(zeff_new)

    #4 should be fine as a limit for Zeff. Lower than usual due to possible lower temperature at the beginning
    # Especially when combined with add profiles early
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] > 1, ids_dict['profiles_1d']['zeff'], 1.02)
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] < 4.0, ids_dict['profiles_1d']['zeff'], 4.0)

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)


def set_impurity_composition_from_flattop(db, shot, run, run_target, db_target = None, shot_target = None, username = None, username_target = None, verbose = False):

    if not username:
        username=getpass.getuser()
    if not db_target:
        db_target = db
    if not shot_target:
        shot_target = shot
    if not username_target:
        username_target = username

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    ip = ids_dict['traces']['global_quantities.ip']
    time = ids_dict['time']['equilibrium']

    # The steady state is identified
    index_start_ft, index_end_ft = identify_flattop_ip(ip, time)

    carbon_density = ids_dict['profiles_1d']['ion[1].density']
    carbon_density_ave = np.average(carbon_density[index_start_ft:index_end_ft], axis = 0)

    # The new carbon density is calculated on the average of the carbon density before the steady state
    carbon_density_new = []

    for carbon_dens in carbon_density[:index_start_ft]:
        carbon_density_new.append(carbon_density_ave)

    for carbon_dens in carbon_density[index_start_ft:index_end_ft]:
        carbon_density_new.append(carbon_dens)

    for carbon_dens in carbon_density[index_end_ft:]:
        carbon_density_new.append(carbon_density_ave)

    # Zeff is calculated normally, the charge is calculated over a profile that considers the lower charge towards the edge. This is TCV specific.
    charge_carbon = []
    rho_tor_norm = ids_dict['profiles_1d']['grid.rho_tor_norm']
    for rho_profile in rho_tor_norm:
        charge_carbon.append(6-2*np.exp(-(5*rho_profile-5)**2))
    charge_carbon = np.asarray(charge_carbon).reshape(len(rho_tor_norm), len(rho_tor_norm[0]))

    n_C = carbon_density_new/ids_dict['profiles_1d']['electrons.density']
    zeff = 1 + n_C*charge_carbon**2 - n_C*charge_carbon

    # Still want to use a flat z_eff profile. This is imposed here

    zeff_new = []
    for z in zeff:
        zeff_new.append(np.full((np.size(z)), np.average(z)))

    ids_dict['profiles_1d']['zeff'] = np.asarray(zeff_new)

    #4 should be fine as a limit for Zeff. Lower than usual due to possible lower temperature at the beginning
    # Especially when combined with add profiles early
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] > 1, ids_dict['profiles_1d']['zeff'], 1.02)
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] < 4.0, ids_dict['profiles_1d']['zeff'], 4.0)

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)



def old_set_impurity_composition_from_flattop(db, shot, run, shot_target, run_target, verbose = False):

    '''

    Sets the impurity content at the beginning (and end) of the simulation as similar to the flattop. Not always advised but it does makes sense in ramp up. At least, for TCV, where the Zeff measurement is not trustworthy at the beginning of the discharge

    '''

    username = getpass.getuser()
    core_profiles = open_and_get_core_profiles(db, shot, run, username)

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    time_start_ft, time_end_ft = identify_flattop(db, shot, run)

    time = ids_dict['time']['core_profiles']

    index_start_ft = np.abs(time - time_start_ft).argmin(0)+1
    index_end_ft = np.abs(time - time_end_ft).argmin(0)-1

    # To find the nearest next time value can also use:
    # next(x[0] for x in enumerate(L) if x[1] > 0.7)

    # Would work generally as a simple method, but I need to find a consistent way to find the impurity averaged charge

    # Will only work for tcv, or other carbon wall machines for which the impurities are set automatically in the ids
    carbon_density = ids_dict['profiles_1d']['ion[1].density']
    # carbon_density_ave = np.average(carbon_density[index_start_ft:index_end_ft], axis = 0)
    carbon_density_ave = np.average(carbon_density[index_start_ft:], axis = 0)

    zeff = ids_dict['profiles_1d']['zeff']
    zeff_ave = np.average(zeff[index_start_ft:index_end_ft], axis = 0)

    zeff_ave = np.average(zeff[index_start_ft:], axis = 0)

    if verbose == True:
        print('The average density of carbon is')
        print(carbon_density_ave)
        print('-------------------------------------------------')

    charge_carbon = 6

    copy_ids_entry(username, db, shot, run, shot_target, run_target)

    # Attaching the average of the flattop at the beginning of the flattop. Could also do it after the flattop but I am not sure it makes physical sense

    # Can calculate the carbon density from zeff or the other way around. The difference is that if the carbon is not fully ionized the zeff can be overestimated in the second case.
    # This is wht method_flag default is 0, underestimation is better here cause zeff is usually overestimated at the beginning. Overestimation can make it too large and crash the simulation

    # ------------------ CHARGE CARBON -----------------------

    rho_tor_norm = ids_dict['profiles_1d']['grid.rho_tor_norm']

    # This kinda works as a decent shape but it should be changed to a properly calculated one when available. Should find a way to input the carbon density and not Zeff

    charge_carbon = []


    for rho_profile in rho_tor_norm:
        charge_carbon.append(6-2*np.exp(-(5*rho_profile-5)**2))

    charge_carbon = np.asarray(charge_carbon).reshape(len(rho_tor_norm), len(rho_tor_norm[0]))

    method_flag = 1

    if method_flag == 1:

        carbon_density_raw, carbon_density_new = [], []

        for carbon_dens in carbon_density[:index_start_ft]:
            carbon_density_raw.append(carbon_density_ave)

        for carbon_dens in carbon_density[index_start_ft:]:
            carbon_density_raw.append(carbon_dens)

# Could do the same at the end of the flattop. It does not seem to be needed though

#        for carbon_dens in carbon_density[index_start_ft:index_end_ft]:
#            carbon_density_new.append(carbon_dens)
#        for carbon_dens in carbon_density[index_end_ft:]:
#            carbon_density_new.append(carbon_density_ave)

        carbon_density_raw = np.asarray(carbon_density_raw)
# It is better to smooth the new profile to avoid large discontinuities

        for time_trace in np.transpose(carbon_density_raw):
            carbon_density_new.append(smooth(time_trace))

        carbon_density_new = np.transpose(np.asarray(carbon_density_new))
        n_C = carbon_density_new/ids_dict['profiles_1d']['electrons.density']
        zeff_new = 1 + n_C*charge_carbon**2 - n_C*charge_carbon

# need to put a lower limit of around 10 eV for the electron and ion temperature at the separatrix. Don't think 1eV is physical...
# Need a more realistic function for charge carbon


    elif method_flag == 0:

        zeff_raw, zeff_new = [], []

        for zeff_profile in zeff[:index_start_ft]:
            zeff_raw.append(zeff_ave)

        for zeff_profile in zeff[index_start_ft:]:
            zeff_raw.append(zeff_profile)

        zeff_raw = np.asarray(zeff_raw)

        for time_trace in np.transpose(zeff_raw):
            zeff_new.append(smooth(time_trace))

        zeff_new = np.transpose(np.asarray(zeff_new))
        n_C = (zeff_new - 1)/(charge_carbon**2 - charge_carbon)
        carbon_density_new = n_C*ids_dict['profiles_1d']['electrons.density']

    if verbose == True:
        fig, axs = plt.subplots(1,2)
        axs[0].plot(ids_dict['time']['core_profiles'], ids_dict['profiles_1d']['ion[1].density'][:,80], 'c-', label = 'nC old')
        axs[1].plot(ids_dict['time']['core_profiles'], ids_dict['profiles_1d']['zeff'][:,80], 'c-', label = 'Zeff old')

    zeff_old = copy.deepcopy(ids_dict['profiles_1d']['zeff'])
    carbon_density_old = copy.deepcopy(ids_dict['profiles_1d']['ion[1].density'])

    for zeff_old_profile, zeff_new_profile, index in zip(zeff_old, zeff_new, range(len(zeff_new))):
        if np.average(zeff_new_profile) < np.average(zeff_old_profile):
            ids_dict['profiles_1d']['zeff'][index] = zeff_new_profile
        else:
            ids_dict['profiles_1d']['zeff'][index] = zeff_old_profile

# The if statement here should act on the same profiles as the one before. If this is not the case, this might be a problem

    for carbon_old_profile, carbon_new_profile, index in zip(carbon_density_old, carbon_density_new, range(len(carbon_density_new))):
        if np.average(carbon_new_profile) < np.average(carbon_old_profile):
            ids_dict['profiles_1d']['ion[1].density'][index] = carbon_new_profile
        else:
            ids_dict['profiles_1d']['ion[1].density'][index] = carbon_old_profile

#    modelling_fields.data_dict['core_profiles']['profiles']['zeff_'] = zeff_new
#    modelling_fields.data_dict['core_profiles']['profiles']['ion_1density'] = carbon_density_new

    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] > 1, ids_dict['profiles_1d']['zeff'], 1.02)
    ids_dict['profiles_1d']['zeff'] = np.where(ids_dict['profiles_1d']['zeff'] < 4.5, ids_dict['profiles_1d']['zeff'], 4.5)

    if verbose == True:
        print(modelling_fields.data_dict['core_profiles']['time'])
        axs[0].plot(ids_dict['time']['core_profiles'], ids_dict['profiles_1d']['ion[1].density'][:,80], 'g-', label = 'nC sub')
        axs[0].plot(ids_dict['time']['core_profiles'], carbon_density_new[:,80], 'r-', label = 'nC new')
        axs[1].plot(ids_dict['time']['core_profiles'], ids_dict['profiles_1d']['zeff'][:,80], 'g-', label = 'Zeff sub')
        axs[1].plot(ids_dict['time']['core_profiles'], zeff_new[:,80], 'r-', label = 'Zeff new')
        fig.legend()
        plt.show()

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

def identify_flattop(db, shot, run, verbose = False):

    '''

    Automatically identifies the flattop. Not very robust but should work for setting Zeff correctly

    '''

    username = getpass.getuser()

    core_profiles = open_and_get_core_profiles(db, shot, run, username)
    summary = open_and_get_summary(db, shot, run, username)

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    if verbose:
        plt.subplot(1,1,1)
        plt.plot(ids_dict['time']['core_profiles'], ids_dict['profiles_1d']['electrons.temperature'][:,0], 'c-', label = 'Te')
        plt.plot(ids_dict['time']['core_profiles'], ids_dict['profiles_1d']['ion[0].temperature'][:,0], 'r-', label = 'Ti')
        plt.legend()
        plt.show()

#    Searching for start and stop of the flattop for various variables. The the start of the flattop is set not to be on the first index

    time_start_ft_te, time_end_ft_te = identify_flattop_variable(ids_dict['profiles_1d']['electrons.temperature'], ids_dict['time']['core_profiles'])
    time_start_ft_ti, time_end_ft_ti = identify_flattop_variable(ids_dict['profiles_1d']['ion[0].temperature'], ids_dict['time']['core_profiles'])

# Removing nan from the ip array. Need to also remove the corresponding times. ip and zeff might be useful for the future or to find mistakes

    ip_map = np.where(np.isnan(summary.global_quantities.ip.value), False, True)

    ip = summary.global_quantities.ip.value[ip_map]
    ip_time = summary.time[ip_map]

    time_start_ft_zeff, time_end_ft_zeff = identify_flattop_variable(ids_dict['profiles_1d']['zeff'], ids_dict['time']['core_profiles'])
    time_start_ft_ip, time_end_ft_ip = identify_flattop_variable(ip, ip_time)
    time_start_ft_ne, time_end_ft_ne = identify_flattop_variable(ids_dict['profiles_1d']['electrons.density'], ids_dict['time']['core_profiles'])

    if verbose:
        print('flattop start and end for Te are ')
        print(time_start_ft_te, time_end_ft_te)
        print('flattop start and end for Ti are ')
        print(time_start_ft_ti, time_end_ft_ti)
        print('flattop start and end for zeff are ')
        print(time_start_ft_zeff, time_end_ft_zeff)
        print('flattop start and end for ne are ')
        print(time_start_ft_ne, time_end_ft_ne)

# The intervals should cross somewhere. Then minimum and maximum are taken. If they do not, an average of start and finish is taken.
# Still kinda ugly but should work. Might want to identify better methods later

    if time_end_ft_te <= time_start_ft_ti or time_end_ft_ti <= time_start_ft_te:
        time_start_ft = (time_start_ft_te + time_start_ft_ti)/2
        time_end_ft = (time_end_ft_te + time_end_ft_ti)/2
    else:
        time_start_ft = max(time_start_ft_te, time_start_ft_ti)
        time_end_ft = min(time_end_ft_te, time_end_ft_ti)

    print('flattop starts and ends at:')
    print(time_start_ft, time_end_ft)

# Might find a better way to include the current start and end of the flattop

    print('current flattop is')
    print(time_start_ft_ip, time_end_ft_ip)
    print('it should be similar. If not, there might be a problem')

    return(time_start_ft, time_end_ft)

#  ------ Should implement, and it might be a good time to try to program the equilibrium interface using attributes ------

#    equilibrium = open_and_get_equilibrium(db, shot, run, username)
#    time_start_ft_ip, time_end_ft_ip = identify_flattop_variable(equilibrium.global_quantities.ip, equilibrium.time)

#    print(time_start_ft_ip, time_end_ft_ip)

def identify_flattop_variable(variables, time):

    '''

    Identifies the flattop for single variables

    '''

    if len(variables.shape) == 2:
        variables = np.average(variables, axis = 1)

    flattop_begin, index_flattop_begin, index_flattop_end = False, 0, len(time)-1
    average, spread = np.average(variables), np.std(variables)/2

#    print(average, spread)

    for index, variable in enumerate(variables):
        if variable > (average - spread) and not flattop_begin and not index == 0:
             index_flattop_begin = index
             flattop_begin = True
        if flattop_begin and variable < (average - spread):
             index_flattop_end = index
             break

    return(time[index_flattop_begin], time[index_flattop_end])

def identify_flattop_ip(ip, time):

    '''

    A more rubust way to identify the steady state for ip
    min_derivative are arbitrary. starting limit_derivative is arbitrary. When derivative is close to 0 I define it as a steady state
    limit derivative is increased is the steady state is too short. Too short is arbitrary, 200ms in the case

    '''

    time_interval, limit_derivative = 0.1, 20000
    if ip[0] > 0:
        ip = -ip

    while time_interval < 0.2:

        smooth_ip = smooth(ip, window_len=17)
        dip_dt = np.gradient(smooth_ip, time)  

        index, index_flattop_begin, index_flattop_end = 0, 0, 0
        while dip_dt[index] < -limit_derivative and index < (len(dip_dt)-1):
            index += 1
        index_flattop_begin = index

        if index == len(dip_dt-1):
            limit_derivative -= 5000
            continue

        while dip_dt[index] > -limit_derivative and dip_dt[index] < limit_derivative and index < (len(dip_dt)-1):
            index += 1
        index_flattop_end = index

        time_interval = time[index_flattop_end] - time[index_flattop_begin]
        limit_derivative += 5000

    return(index_flattop_begin, index_flattop_end)


def check_ion_number(db, shot, run):

    core_profiles = open_and_get_core_profiles(db, shot, run)
    ion_number = len(core_profiles.profiles_1d[0].ion)

    return(ion_number)

# ------------------------------- Q PROFILE MANIPULATION ---------------------------------

def flip_q_profile(db, shot, run, run_target, username = ''):

    '''

    Writes a new ids with the opposite sign of the q profile

    '''
    if username == '':
        username = getpass.getuser()

    core_profiles = open_and_get_core_profiles(db, shot, run, username)

    for index, profile_1d in enumerate(core_profiles.profiles_1d):
        core_profiles.profiles_1d[index].q = -core_profiles.profiles_1d[index].q

    copy_ids_entry(username, db, shot, run, shot, run_target)

    data_entry_target = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run_target, user_name=username)

    op = data_entry_target.open()
    core_profiles.put(db_entry = data_entry_target)
    data_entry_target.close()

def use_flat_q_profile(db, shot, run, run_target, username = ''):

    '''

    Writes a new ids with a flat q profile

    '''
    if username == '':
        username = getpass.getuser()

    core_profiles = open_and_get_core_profiles(db, shot, run, username)
    q = []

    len_time = len(core_profiles.time)
    len_x = len(core_profiles.profiles_1d[0].q)
    q_edge_1 = core_profiles.profiles_1d[0].q[-1]

    q = np.full((len_time, len_x), q_edge_1)

    for index, q_slice in enumerate(q):
        core_profiles.profiles_1d[index].q = q_slice

    copy_ids_entry(username, db, shot, run, shot, run_target)

    data_entry_target = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run_target, user_name=username)

    op = data_entry_target.open()
    core_profiles.put(db_entry = data_entry_target)
    data_entry_target.close()

def use_flat_vloop(db, shot, run_relaxed, run_target, username = ''):

    '''

    Substitute the q profile from a run where the q profile was relaxed.
    Such run should be specified

    '''

    if username == '':
        username = getpass.getuser()

    core_profiles = open_and_get_core_profiles(db, shot, run_relaxed, username)
    q_slice = core_profiles.profiles_1d[-1].q

    for index, q_slice in enumerate(q):
        core_profiles.profiles_1d[index] = q_slice

    copy_ids_entry(username, db, shot, run_relaxed, shot_target, run_target)

    data_entry_target = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run_target, user_name=username)

    op = data_entry_target.open()
    core_profiles.put(db_entry = data_entry_target)
    data_entry_target.close()


def check_and_flip_ip(db, shot, run, shot_target, run_target):

    equilibrium = open_and_get_equilibrium(db, shot, run)
    if equilibrium.time_slice[0].global_quantities.ip > 0:
        flip_ip(db, shot, run, shot_target, run_target)

        print('ip was positive for shot ' + str(shot) + ' and was flipped to negative')

def flip_ip(db, shot, run, shot_target, run_target):

    username = getpass.getuser()

    equilibrium = open_and_get_equilibrium(db, shot, run)
    copy_ids_entry(username, db, shot, run, shot_target, run_target)

    equilibrium_new = copy.deepcopy(equilibrium)

    for itime, time_slice in enumerate(equilibrium.time_slice):
        equilibrium_new.time_slice[itime].global_quantities.ip = -equilibrium.time_slice[itime].global_quantities.ip

    equilibrium_new.vacuum_toroidal_field.b0 = -equilibrium.vacuum_toroidal_field.b0

    data_entry_target = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot_target, run_target, user_name=getpass.getuser())

    op = data_entry_target.open()
    equilibrium_new.put(db_entry = data_entry_target)
    data_entry_target.close()

# ------------------------------- KINETIC PROFILES MANIPULATION ---------------------------------

def peak_temperature(db, shot, run, db_target, shot_target, run_target, username = '', username_target = '', mult = 1):

    '''

    Writes a new IDS with a more (or less) peaked electron temperature profile. The value at the boundary is kept constant. The new version is still untested

    '''

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    e_temperatures = ids_dict['profiles_1d']['electrons.temperature']
    new_e_temperature = []

    for e_temperature in e_temperatures:
        new_e_temperature.append(mult*(e_temperature - e_temperature[-1]) + e_temperature[-1])

    ids_dict['profiles_1d']['electrons.temperature'] = np.asarray(new_e_temperature)

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

    print('temperature_peaked')

def correct_boundaries_te(db, shot, run, db_target, shot_target, run_target, username = '', username_target = '', verbose = False):

    '''

    Writes a new IDS with a corrected value at the boundaries. With 'corrected' it is meant a value larger than 20 eV, since I
    do not think that a lower value at the separatrix would be physical. The boundary is raised and then everything is shifted linearly.
    The same value is kept for the axis. The same is done for the ion temperature

    '''

    if username == '':
        username=getpass.getuser()

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    e_temperatures = ids_dict['profiles_1d']['electrons.temperature']
    i_temperatures = ids_dict['profiles_1d']['t_i_average']
    rhos = ids_dict['profiles_1d']['grid.rho_tor_norm']

    new_e_temperatures, new_i_temperatures = [], []

    for rho, e_temperature, index in zip(rhos, e_temperatures, range(len(rhos))):
        if e_temperature[-1] < 20:
            new_e_temperatures.append(e_temperature+(20-e_temperature[-1])*rho)
            index_modified = index
        else:
            new_e_temperatures.append(e_temperature)

    for rho, i_temperature, index in zip(rhos, i_temperatures, range(len(rhos))):
        if i_temperature[-1] < 20:
            new_i_temperatures.append(i_temperature+(20-i_temperature[-1])*rho)
            index_modified = index
        else:
            new_i_temperatures.append(i_temperature)

    new_e_temperatures = np.asarray(new_e_temperatures).reshape(len(e_temperatures),len(e_temperatures[0]))
    ids_dict['profiles_1d']['electrons.temperature'] = new_e_temperatures

    new_i_temperatures = np.asarray(new_i_temperatures).reshape(len(i_temperatures),len(i_temperatures[0]))
    ids_dict['profiles_1d']['t_i_average'] = new_i_temperatures
    # Not really needed but trying to maintain consistency in case is needed later. Might put a loop later, only 2 imp supported now
    ids_dict['profiles_1d']['ion[0].temperature'] = new_i_temperatures
    ids_dict['profiles_1d']['ion[1].temperature'] = new_i_temperatures

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

    if verbose and index_modified:
        fig, axs = plt.subplots(1,1)
        axs.plot(rhos[index_modified], e_temperatures[index_modified], 'r-', label = 'Te old')
        axs.plot(rhos[index_modified], new_e_temperatures[index_modified], 'b-', label = 'Te new')
        fig.legend()
        plt.show()

    print('Boundaries corrected')



def set_boundaries_te(db, shot, run, run_target, te_sep, ti_sep = None, method = 'constant', db_target = None, shot_target = None, username = ''):

    '''

    Writes a new IDS with a corrected value at the boundaries. With 'corrected' it is meant a value larger than 20 eV, since I
    do not think that a lower value at the separatrix would be physical. The boundary is raised and then everything is shifted linearly.
    The same value is kept for the axis. The same is done for the ion temperature

    '''

    if username == '': username = getpass.getuser()
    if not db_target: db_target = db
    if not shot_target: shot_target = shot
    if not ti_sep: ti_sep = te_sep

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    e_temperatures = ids_dict['profiles_1d']['electrons.temperature']
    i_temperatures = ids_dict['profiles_1d']['t_i_average']
    rhos = ids_dict['profiles_1d']['grid.rho_tor_norm']
    times = ids_dict['time']['core_profiles']

    te_sep_time, ti_sep_time = [], []
    for itime, time in enumerate(times):
        if method == 'constant':
            te_sep_time.append(te_sep)
            if ti_sep:
                ti_sep_time.append(ti_sep)
        elif method == 'linear':
            if te_sep is list and ti_sep is list:
                te_sep_time.append((ti_sep[1]-te_sep[0])*(time-time[0])/time[-1])
                if ti_sep:
                    ti_sep_time.append((ti_sep[1]-ti_sep[0])*(time-time[0])/time[-1])
            else:
                print('te and ti sep need to be lists with the first and the last value when method is linear. Aborting')
                exit()
        elif method == 'add':
            te_sep_time.append(e_temperatures[itime][-1] + te_sep)
            if ti_sep:
                ti_sep_time.append(e_temperatures[itime][-1] + ti_sep)
        else:
            print('method for boundary settings not recognized. Aborting')
            exit()


    new_e_temperatures, new_i_temperatures = [], []

    for rho, e_temperature, index in zip(rhos, e_temperatures, range(len(rhos))):
        new_e_temperatures.append(e_temperature+(te_sep_time[index]-e_temperature[-1])*rho)

    for rho, i_temperature, index in zip(rhos, i_temperatures, range(len(rhos))):
        new_i_temperatures.append(i_temperature+(ti_sep_time[index]-i_temperature[-1])*rho)

    new_e_temperatures = np.asarray(new_e_temperatures).reshape(len(e_temperatures),len(e_temperatures[0]))
    ids_dict['profiles_1d']['electrons.temperature'] = new_e_temperatures

    new_i_temperatures = np.asarray(new_i_temperatures).reshape(len(i_temperatures),len(i_temperatures[0]))
    ids_dict['profiles_1d']['t_i_average'] = new_i_temperatures
    # Not really needed but trying to maintain consistency in case is needed later. Might put a loop later, only 2 imp supported now
    ids_dict['profiles_1d']['ion[0].temperature'] = new_i_temperatures
    ids_dict['profiles_1d']['ion[1].temperature'] = new_i_temperatures

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

    print('Set boundaries completed')


def alter_q_profile_same_q95(db, shot, run, db_target, shot_target, run_target, username = '', username_target = '', mult = 1):

    '''

    Writes a new IDS with the same q95, but changing the value of q0. This version is untested

    '''

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict


    # Changing the q profile both in equilibrium and core profiles
    q_new = []
    for q_slice, rho_slice in zip(ids_dict['profiles_1d']['profiles_1d.q'], ids_dict['profiles_1d']['profiles_1d.rho_tor_norm']):
        q_slice = q_slice*((1-mult)/0.95*rho_slice + mult)
        q_new.append(q_slice)

    ids_dict['profiles_1d']['profiles_1d.q'] = np.asarray(q_new)

    q_new = []
    for q_slice, rho_slice in zip(ids_dict['profiles_1d']['q'], ids_dict['profiles_1d']['grid.rho_tor_norm']):
        q_slice = q_slice*((1-mult)/0.95*rho_slice + mult)
        q_new.append(q_slice)

    ids_dict['profiles_1d']['q'] = np.asarray(q_new)

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

def shift_profiles(profile_tag, db, shot, run, db_target, shot_target, run_target, username = '', username_target = '', mult = 1):

    '''

    Multiplies the profiles for all timeslices for a fixed value. Needs a tag to work (TE, NE, TI, ZEFF)

    '''

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    if profile_tag == 'TE':
        dict_key = 'electrons.temperature'
    elif profile_tag == 'NE':
        dict_key = 'electrons.density'
    elif profile_tag == 'TI':
        dict_key = 'ion[0].temperature'
    elif profile_tag == 'ZEFF':
# Modified and untested. Not sure it maintains ambipolarity by default
        dict_key = 'ion[1].density'
#        dict_key = 'zeff'

# Could also use lists for everything and use only one of these. For example, electron pressure should also be changed.

    if dict_key == 'ion[0].temperature':
        ion_temperature_keys = ['ion[0].temperature', 'ion[0].pressure_thermal', 'ion[1].temperature', 'ion[1].pressure_thermal', 't_i_average']
        for key in ion_temperature_keys:

            new_profiles = copy.deepcopy(ids_dict['profiles_1d'][key])
            for index, profile in enumerate(ids_dict['profiles_1d'][key]):
                new_profiles[index] = mult*profile

            ids_dict['profiles_1d'][key] = new_profiles

    elif dict_key == 'electrons_density':
        density_keys = ['electrons.density', 'electrons.density_thermal']
        for key in density_keys:

            new_profiles = copy.deepcopy(ids_dict['profiles_1d'][key])
            for index, profile in enumerate(ids_dict['profiles_1d'][key]):
                new_profiles[index] = mult*profile

            ids_dict['profiles_1d'][key] = new_profiles

    else:
        new_profiles = copy.deepcopy(ids_dict['profiles_1d'][dict_key])

        for index, profile in enumerate(ids_dict['profiles_1d'][dict_key]):
            new_profiles[index] = mult*profile

        ids_dict['profiles_1d'][dict_key] = new_profiles

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)

def add_early_profiles(db, shot, run, run_target, db_target = None, shot_target = None, username = None, username_target = None):

    '''

    Inserts time_slices at the beginning of core_profiles, to try to model the early stages.
    No normalization to energy diamagnetic is done right now. Agreement with the profiles is not always great, so need to think what to do there
    For now a flat te profile is imposed at 0.01, using the last boundary value.

    '''

    if not username:
        username = getpass.getuser()
    if not username_target:
        username_target = username
    if not db_target:
        db_target = db
    if not shot_target:
        shot_target = shot

    ids_data = IntegratedModellingDict(db, shot, run, username = username)
    ids_dict = ids_data.ids_dict

    old_times = ids_dict['time']['core_profiles']
    new_times = old_times[:]
    
    while new_times[0] > 0.01:
        new_times = np.insert(new_times, 0, new_times[0] - (new_times[1] - new_times[0]))

    old_times = np.insert(old_times, 0, 0.0)
    new_profiles = {}

    for variable in ['electrons.density_thermal', 'electrons.density', 'electrons.temperature', 'q', 't_i_average']:

        old_profiles = ids_dict['profiles_1d'][variable]
        first_profile = np.full(np.size(ids_dict['profiles_1d'][variable][0]), ids_dict['profiles_1d'][variable][0][-1])
        old_profiles = np.insert(old_profiles, 0, first_profile, axis = 0)

        x_dim = np.shape(old_profiles)[1]
        time_dim = np.shape(old_profiles)[0]
        new_profiles[variable] = np.asarray([])

        for i in np.arange(x_dim):
            if np.size(new_profiles[variable]) != 0:
                new_profiles[variable] = np.hstack((new_profiles[variable], fit_and_substitute(old_times, new_times, old_profiles[:,i])))
            else:
                new_profiles[variable] = fit_and_substitute(old_times, new_times, old_profiles[:,i])

        new_profiles[variable] = new_profiles[variable].reshape(x_dim, len(new_times))

    ids_data.update_times(new_times, ['core_profiles'])
    
    # The fit in time of rho tor norm might mix the grid, which needs to be sorted.
    new_rho_tor_norm = np.asarray([])

    for rho_tor_norm_profile in ids_data.ids_dict['profiles_1d']['grid.rho_tor_norm']:
        if np.size(new_rho_tor_norm) != 0:
            new_rho_tor_norm = np.hstack((new_rho_tor_norm, np.sort(rho_tor_norm_profile)/max(rho_tor_norm_profile)))
        else:
            new_rho_tor_norm = np.sort(rho_tor_norm_profile)/max(rho_tor_norm_profile)

    ids_dict['profiles_1d']['grid.rho_tor_norm'] = new_rho_tor_norm.reshape(len(new_times), x_dim)
    
    for variable in ['electrons.density_thermal', 'electrons.density', 'electrons.temperature', 'q', 't_i_average']:
        ids_dict['profiles_1d'][variable] = np.transpose(np.asarray(new_profiles[variable]))

    ids_data.ids_dict = ids_dict
    ids_data.fill_ids_struct()

    put_integrated_modelling(db, shot, run, run_target, ids_data.ids_struct)


# -------------------------------- EXTRA TOOLS TO MAKE THE REST WORK -------------------------------------

class Parser(xml.sax.handler.ContentHandler):
    def __init__(self):
        xml.sax.handler.ContentHandler.__init__(self)
        self.idss = []

    def startElement(self, name, attrs):
        if name == 'IDS':
            ids = dict()
            for i in attrs.getNames():
                ids[i] = attrs.getValue(i)
            self.idss.append(ids)


def fit_and_substitute(x_old, x_new, data_old):

    f_space = interp1d(x_old, data_old, fill_value = 'extrapolate')

    variable = np.array(f_space(x_new))
    variable[variable > 1.0e25] = 0

    return variable

def fit_and_substitute_nbi(x_old, x_new, data_old):

    f_space = interp1d(x_old, data_old, bounds_error = False, fill_value = 0)

    variable = np.array(f_space(x_new))
    variable[variable > 1.0e25] = 0

    return variable

def double_time(times):

    '''

    Insert middle times in a time array

    '''

    time_doubled = []

    for time_pre, time in zip(times, times[1:]):
        time_doubled.append(time_pre)
        time_doubled.append(time_pre+(time - time_pre)/2)

    time_doubled.append(times[-1])
    time_doubled.append(times[-1]+(times[-1] - times[-2])/2)

    return(time_doubled)


def create_line_list():

    color_list = 'b', 'g', 'r', 'c', 'm', 'y','k'
    line_list = '-', '--', '-.', ':', '.'

    style_list = []
    for line in line_list:
        for color in color_list:
            style_list.append(color+line)

    return style_list

def get_label(profile_tag):

    if profile_tag in profile_tag_list:
        y_label, units = profile_tag_list[profile_tag][0], profile_tag_list[profile_tag][1]
    else:
        y_label, units = profile_tag, '[-]'

    return y_label, units

def smooth(x,window_len=7,window='hanning'):
    """smooth the data using a window with requested size.

    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.

    input:
        x: the input signal
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal

    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)

    see also:

    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter

    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """
    if x.ndim != 1:
        print('smooth only accepts 1 dimension arrays.')
        raise ValueError

    if x.size < window_len:
        print('Input vector needs to be bigger than window size.')
        raise ValueError

    if window_len<3:
        return x

    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        print('Window is on of \'flat\', \'hanning\', \'hamming\', \'bartlett\', \'blackman\'')
        raise ValueError


    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')

    return y[int(window_len/2+1):-int(window_len/2-1)]

def copy_ids_entry(username, db, shot, run, shot_target, run_target, ids_list = []):

    '''

    Copies an entire IDS entry

    '''

    if username == '':
        username = getpass.getuser()

    # open input pulsefile and create output one

# path hardcoded for now, not ideal but avoids me to insert the version everytime. Might improve later
    path = '/gw/swimas/core/installer/src/3.34.0/ual/4.9.3/xml/IDSDef.xml'
    parser = Parser()
    xml.sax.parse(path, parser)

    vsplit = imas.names[0].split("_")
    imas_version = version.parse(".".join(vsplit[1:4]))
    imas_major_version = str(imas_version)[0]
    ual_version = version.parse(".".join(vsplit[5:]))

    print('Opening', username, db, imas_version, shot, run)
    idss_in = imas.ids(shot, run)
    op = idss_in.open_env(username, db, imas_major_version)

    if op[0]<0:
        print('The entry you are trying to copy does not exist')
        exit()

    print('Creating', username, db, imas_version, shot_target, run_target)
    idss_out = imas.ids(shot_target, run_target)
    idss_out.create_env(username, db, imas_major_version)
    idx = idss_out.expIdx
    ids_list = None
    # read/write every IDS

    for ids_info in parser.idss:
        name = ids_info['name']
        maxoccur = int(ids_info['maxoccur'])
        if ids_list and name not in ids_list:
            continue
        if name == 'ec_launchers' or name == 'numerics' or name == 'sdn':
#        if name == 'ec_launchers' or name == 'numerics' or name == 'sdn' or name == 'nbi':    # test for nbi ids, temporary
            continue
            print('continue on ec launchers')  # Temporarily down due to a malfunctioning of ec_launchers ids
            print('skipping numerics')  # Not in the newest version of IMAS
        for i in range(maxoccur + 1):
            if not i:
                print('Processing', ids_info['name'])
#            if i:
#                print('Processing', ids_info['name'], i)
#            else:
#                print('Processing', ids_info['name'])

            ids = idss_in.__dict__[name]
            stdout = sys.stdout
            sys.stdout = open('/afs/eufus.eu/user/g/g2mmarin/warnings_imas.txt', 'w') # suppress warnings
            ids.get(i)
#            sys.stdout = stdout
            ids.setExpIdx(idx)
            ids.put(i)
            sys.stdout.close()
            sys.stdout = stdout

    idss_in.close()
    idss_out.close()

# -------------------------------- LISTS OF KEYS -------------------------------------

keys_list = {
    'traces': {},
    'profiles_1d': {},
    'profiles_2d': {}
}

ids_list = [
    'core_profiles',
    'core_sources',
    'ec_launchers',
    'equilibrium',
#    'nbi',
    'summary',
    'thomson_scattering'
]

keys_list['profiles_2d']['core_profiles'] = [
]

keys_list['profiles_1d']['core_profiles'] = [
    'q',
    'electrons.density_thermal',
    'electrons.density',
    'electrons.temperature',
    'ion[].temperature',
    'ion[].density',
    't_i_average',
    'zeff',
    'grid.rho_tor_norm'
]

keys_list['traces']['core_profiles'] = [
    'ip',
    'v_loop',
    'li_3',
    'energy_diamagnetic',
    'ion[].z_ion',
    'ion[].multiple_states_flag',
# This might break when interpolating (It should not, but it is still untested)
    'ion[].label',
# These two are new and might break things
    'ion[].element[].a',
    'ion[].element[].z_n',
    'ion[].element[].atoms_n'
]
# This list should be passed to the pulse_schedule IDS
keys_list['profiles_1d']['summary'] = []
keys_list['traces']['summary'] = [
    'global_quantities.ip.value',
    'heating_current_drive.power_nbi.value',
    'heating_current_drive.power_ic.value',
    'heating_current_drive.power_ec.value',
    'heating_current_drive.power_lh.value',
    'stationary_phase_flag.value',
    'line_average.n_e.value',
    'global_quantities.v_loop.value',
    'global_quantities.li.value',
    'global_quantities.li_mhd.value',
    'global_quantities.energy_diamagnetic.value',
    'global_quantities.energy_mhd.value',
    'global_quantities.energy_thermal.value',
    'global_quantities.beta_pol.value',
    'global_quantities.beta_pol_mhd.value',
    'global_quantities.beta_tor_norm.value',
    'global_quantities.power_radiated.value',
    'fusion.neutron_fluxes.total.value'
]

keys_list['profiles_1d']['equilibrium'] = [
    'profiles_1d.psi',
    'profiles_1d.f',
    'profiles_1d.q',
    'profiles_1d.pressure',
    'profiles_1d.rho_tor_norm',
    'boundary.outline.r',
    'boundary.outline.z',
    'profiles_2d[].grid.dim1',
    'profiles_2d[].grid.dim2'
]

keys_list['traces']['equilibrium'] = [
    'global_quantities.ip',
    'global_quantities.li_3',
    'global_quantities.beta_pol',
    'global_quantities.beta_tor',
    'global_quantities.magnetic_axis.r',
    'global_quantities.magnetic_axis.z',
    'profiles_2d[].grid_type.name',
    'profiles_2d[].grid_type.index'
]

keys_list['profiles_2d']['equilibrium'] = ['profiles_2d[].psi']

keys_list['profiles_1d']['core_sources'] = [
    'total#electrons.energy',
    'total#total_ion_energy',
    'total#j_parallel',
    'total#momentum_tor',
    'total#ion[].particles',
    'total#grid.rho_tor_norm',
    'nbi#electrons.energy',
    'nbi#total_ion_energy',
    'nbi#j_parallel',
    'nbi#momentum_tor',
    'nbi#ion[].particles',
    'nbi#grid.rho_tor_norm',
    'ec#electrons.energy',
    'ec#total_ion_energy',
    'ec#j_parallel',
    'ec#momentum_tor',
    'ec#ion[].particles',
    'ec#grid.rho_tor_norm',
    'lh#electrons.energy',
    'lh#total_ion_energy',
    'lh#j_parallel',
    'lh#momentum_tor',
    'lh#ion[].particles',
    'lh#grid.rho_tor_norm',
    'ic#electrons.energy',
    'ic#total_ion_energy',
    'ic#j_parallel',
    'ic#momentum_tor',
    'ic#ion[].particles',
    'ic#grid.rho_tor_norm'
]

keys_list['traces']['core_sources'] = [
    'total#ion[].element[].a',
    'total#ion[].element[].z_n',
    'total#ion[].element[].atoms_n',
    'nbi#ion[].element[].a',
    'nbi#ion[].element[].z_n',
    'nbi#ion[].element[].atoms_n',
    'ec#ion[].element[].a',
    'ec#ion[].element[].z_n',
    'ec#ion[].element[].atoms_n',
    'lh#ion[].element[].a',
    'lh#ion[].element[].z_n',
    'lh#ion[].element[].atoms_n',
    'ic#ion[].element[].a',
    'ic#ion[].element[].z_n',
    'ic#ion[].element[].atoms_n'
]

#keys_list['traces']['nbi'] = ['unit[]energy.data']
#keys_list['profiles_1d']['nbi'] = ['unit[]beam_power_fraction.data']

keys_list['traces']['ec_launchers'] = []
keys_list['profiles_1d']['ec_launchers'] = []

keys_list['traces']['thomson_scattering'] = []
keys_list['profiles_1d']['thomson_scattering'] = []

profile_tag_list = {
    'q_' : ['q profile', '[-]'],
    'electrons_temperature' : ['electron temperature', '[eV]'],
    't_i_average' : ['ion temperature', '[eV]'],
    'electrons_density' : ['electron density', r'[$m^{-3}$]']
}











