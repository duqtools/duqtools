import json
import os,datetime,sys
import shutil
import getpass
import numpy as np
import pickle
import math
import functools
import re
from scipy import integrate
from scipy.interpolate import interp1d, UnivariateSpline
import idstools
#from idstools import *
from packaging import version
from os import path

import inspect
import types

import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation
from IPython import display

import xml.sax
import xml.sax.handler

'''
The tools in this script are useful to:

Setup integrated modelling simulations
Setup sensitivities
Run sensitivities
Compare integrated modelling with experimental data
'''

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

#    print(imas_version)
#    print(ual_version)

#from tools_input_im import *
import jetto_tools

import copy

'''

--------------- AVAILABLE FUNCTIONS: ------------------

1 - setup_input_baserun(verbose = False):
2 - setup_input_sensitivities()
3 - create_baserun()
4 - create_sensitivities(force_run = False)
5 - run_baserun()
6 - run_sensitivities(force_run = False)

Steps nesessary:
1 - Setup the input for a baserun
2 - Setup the input for a sensitivity
3 - Create the baserun folder
4 - Create the sensitivities folders
5 - Run the baserun
6 - Run the sensitivities


# Setting up a single folder ready for integrated modelling
setup_jetto_simulation()
setup_feedback_on_density()


# Tools: modify the jset and llcmd files
modify_jset(path, sensitivity_name, ids_number, ids_output_number, db, username, shot)
modify_jset_line(sensitivity_name, line_start, new_content)
modify_llcmd(sensitivity_name, baserun_name)

# Small utilities, hopefully temporary
check_and_flip_ip(db, shot, run, shot_target, run_target)
flip_ip(db, shot, run, shot_target, run_target)


'''

class IntegratedModellingRuns:
    def __init__(
	self, 
	shot, 
	instructions_list, 
	generator_name, 
	baserun_name, 
	db = 'tcv', 
	run_input = 1,
        run_start = None,
	run_output = 100,
	time_start = 0,
	time_end = 100,
        esco_timesteps = None,
        output_timesteps = None,
	force_run = False,
	density_feedback = False,
        pulse_scheduler = False,
	zeff_option = None,
        zeff_mult = 1,
        sensitivity_list = [],
        input_instructions = [],
        boundary_instructions = {}
    ):

        # db is the name of the machine. Needs to be the name of the imas database.
        # shot is the shot number. It is an int.
        # run input is where the input is. It will not be the input for the simulations though, since it needs to be massaged
        # run output is the output number for the baserun. The sensitivities will start here and increase by 1 as in the list
        # generator name is the name of the generator as it appears in the run folder

        self.username = getpass.getuser()
        self.db = db
        self.shot = shot
        self.run_input = run_input
        self.run_start = run_start
        self.run_output = run_output
        self.time_start = time_start
        self.time_end = time_end
        self.esco_timesteps = esco_timesteps
        self.output_timesteps = output_timesteps
        self.force_run = force_run
        self.density_feedback = density_feedback
        self.pulse_scheduler = pulse_scheduler
        self.core_profiles = None
        self.equilibrium = None
        self.line_ave_density = None
        self.input_instructions = input_instructions
        self.sensitivity_list = sensitivity_list
        self.zeff_option = zeff_option
        self.zeff_mult = zeff_mult
        self.boundary_instructions = boundary_instructions

        # Trying to be a little flexible with the generator name. It is not used if I am only setting the input.
        # Still mandatory argument, should not be forgotten

        self.path = '/pfs/work/' + self.username + '/jetto/runs/'
        self.generator_username = ''

        if generator_name.startswith('/pfs/work'):
            self.path_generator = generator_name
            self.generator_name = generator_name.split('/')[-2]
            self.generator_username = generator_name.split('/')[3]
        elif generator_name.startswith('rungenerator_'):
            self.generator_name = generator_name
            self.path_generator = self.path + self.generator_name
            self.generator_username = self.username  # new
        else:
            self.generator_name = 'rungenerator_' + generator_name
            self.path_generator = self.path + self.generator_name
            self.generator_username = self.username # new

        self.baserun_name = baserun_name

        # Default instructions: do nothing
        self.instructions = {
            'setup base' : False,
            'setup sens' : False,
            'create base' : False,
            'create sens' : False,
            'run base' : False,
            'run sens' : False
        }

        for key in instructions_list:
            if key in self.instructions:
                self.instructions[key] = True

        # Default sensitivity list. The sensitivity list can be omitted and will not be used when only dealing with the baserun

        # Example of sensitivity list. Not default.
        #if not sensitivity_list:
        #    self.sensitivity_list = ['te 0.8', 'te 1.2', 'ne 0.8', 'ne 1.2', 'zeff 0.8', 'zeff 1.2', 'q95 0.8', 'q95 1.2']

        # Default baserun name is 'run000'. It is not used if I am only setting the input. Baserun name should always start with 'run###'

        if self.baserun_name == '':
            self.baserun_name = 'run000'  + str(self.shot) + 'base'

        self.path_baserun = self.path + self.baserun_name

        self.tag_list = []
        for sensitivity in self.sensitivity_list:
            tag = sensitivity.replace(' ', '_')
            tag = tag.replace('.', '_')
            tag = '_' + tag
            self.tag_list.append(tag)

        # New instructions are just an array with six True/False (or 0/1). They correspond orderly to what to do in the instruction list

    def update_instructions(self, new_instructions):

        for i, key in enumerate(self.instructions):
            self.instructions[key] = new_instructions[i]

    def update_sensitivities(self, new_sensitivities_list):

        self.sensitivity_list = new_sensitivities_list

    def setup_create_compare(self, verbose = False):


        # Could use the list directly but this should be more readable. instructions_list needs to be a list of six values, connected with the instructions
        # Put checks on the list to make sure that is fool proof

        if self.instructions['setup base']:
            self.setup_input_baserun(verbose = False)
        if self.instructions['setup sens']:
            self.setup_input_sensitivities()
        if self.instructions['create base']:
            self.create_baserun()
        if self.instructions['create sens']:
            self.create_sensitivities()
        if self.instructions['run base']:
            self.run_baserun()
        if self.instructions['run sens']:
            self.run_sensitivities()

    def setup_input_baserun(self, verbose = False):
    
        '''
    
        Modified the setup function to have it in a separate file as an extra option. The new script can be used standalone.
        If the setup is not used importing the script will not be necessary    

        '''

        try:
            import prepare_im_input
        except ImportError:
            print('prepare_input.py not found and needed for this option. Aborting')
            exit()

        self.core_profiles, self.equilibrium = prepare_im_input.setup_input(self.db, self.shot, self.run_input, self.run_start, zeff_option = self.zeff_option, zeff_mult = self.zeff_mult, instructions = self.input_instructions, boundary_instructions = self.boundary_instructions, time_start = self.time_start, time_end = self.time_end, core_profiles = self.core_profiles, equilibrium = self.equilibrium)


    def setup_input_sensitivities(self):
    
        '''
    
        Automatically sets up the IDSs to be used as an input for a sensitivity study. More sensitivities can be added
    
        '''
    
        try:
            import prepare_im_input
        except ImportError:
            print('prepare_input.py not found and needed for this option. Aborting')
            exit()

    # Maybe here I am already creating all the entries, which might be a problem if I change 'shift profiles', but should be allright for now

        for index in range(1,len(self.tag_list),1):
            data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, self.db, self.shot, self.run_start+index, user_name=self.username)
            op = data_entry.open()
    
            if op[0]==0:
                print('one of the data entries already exists, aborting')
                exit()
    
            data_entry.close()
    
        # Could check that there are no idss here before I overwrite evverything
    
        name, mult = [], []
    
    # Give the option to the user to decide which sensitivities should be done
    
        index = 1

        for run in self.sensitivity_list:
            name, mult = run.split(' ')
            name = name
            mult = float(mult)
    
            if name == 'te':
                print(self.db, self.shot, self.run_start)
                prepare_im_input.shift_profiles('TE', self.db, self.shot, self.run_start, self.db, self.shot, self.run_start+index, mult = mult)
            if name == 'ti':
                prepare_im_input.shift_profiles('TI', self.db, self.shot, self.run_start, self.db, self.shot, self.run_start+index, mult = mult)
            if name == 'ne':
                prepare_im_input.shift_profiles('NE', self.db, self.shot, self.run_start, self.db, self.shot, self.run_start+index, mult = mult)
            if name == 'zeff':
                prepare_im_input.shift_profiles('ZEFF', self.db, self.shot, self.run_start, self.db, self.shot, self.run_start+index, mult = mult)
            if name == 'tepeak':
                prepare_im_input.peak_temperature(self.db, self.shot, self.run_start, self.db, self.shot, self.run_start+index, mult = mult)
            if name == 'q95':
                prepare_im_input.alter_q_profile_same_q95(self.db, self.shot, self.run_start, self.db, self.shot, self.run_start+index, mult = mult)
    
            index += 1
    
    def create_baserun(self):
    
        '''
    
        Automatically sets up the folder for the baserun of a specific scan.
        The type of the baserun will determine which kind of runs the sensitivity should be carried out from. Default options are given
    
        '''
  
        os.chdir(self.path)

        if os.path.exists(self.path_generator):
            shutil.copytree(self.path_generator, self.path_baserun)
        else:
            print('generator not recognized. Aborting')
            exit()

        b0, r0, start_time, end_time = self.get_r0_b0()

        if self.density_feedback == True:
            self.get_feedback_on_density_quantities()        

        # To save time, equilibrium and core profiles are not extracted if they already exist
        if not self.core_profiles:
            self.core_profiles = open_and_get_core_profiles(self.db, self.shot, self.run_input)

        if not self.equilibrium:
            self.equilibrium = open_and_get_equilibrium(self.db, self.shot, self.run_input)

        # This should not be needed and should be handled by the jetto_tools. It's not though...
        # This is untested and might break
        imp_data = []
        first_imp_density = None
        for ion in self.core_profiles.profiles_1d[0].ion:
            imp_density = np.average(ion.density)
            z_ion = ion.element[0].z_n
            a_ion = ion.element[0].a
            z_bundle = round(z_ion)
            if z_ion > 1:
                if not first_imp_density:
                    imp_relative_density = 1.0
                    first_imp_density = imp_density
                else:
                    imp_relative_density = first_imp_density/imp_density

                imp_data.append([imp_relative_density, a_ion, z_bundle, z_ion])

#        imp_data = [[1.0, 12.0, 6, 6.0]]

        if (b0 > 0 and self.equilibrium.time_slice[0].global_quantities.ip < 0) or (b0 < 0 and self.equilibrium.time_slice[0].global_quantities.ip > 0):
            ibtsign = 1
        else:
            ibtsign = -1

        if 'interpretive' not in self.path_generator:
            interpretive_flag = False
        else:
            interpretive_flag = True

        # Still cannot run with positive current...
        self.modify_jetto_in(self.baserun_name, r0, abs(b0), start_time, end_time, imp_datas_ids = imp_data, num_times_print = self.output_timesteps, num_times_eq = self.esco_timesteps, ibtsign = ibtsign, interpretive_flag = interpretive_flag)
        #self.modify_jetto_in(self.baserun_name, r0, b0, start_time, end_time, imp_datas_ids = imp_data, num_times_print = self.output_timesteps, ibtsign = ibtsign)

        self.setup_jetto_simulation()
    
        if self.density_feedback == True:
            self.setup_feedback_on_density(self.run_input)

        self.modify_jset(self.path, self.baserun_name, self.run_start, self.run_output, abs(b0), r0)
        #self.modify_jset(self.path, self.baserun_name, self.run_start, self.run_output, b0, r0)

        # Selecting the impurity correctly in the jset

        impurity_jset_linestarts = ['ImpOptionPanel.impuritySelect[]',
                                    'ImpOptionPanel.impurityMass[]',
                                    'ImpOptionPanel.impurityCharge[]',
                                    'ImpOptionPanel.impuritySuperStates[]'
                                   ]
        for index in range(6):
            if index < len(imp_data):
                for jset_linestart in impurity_jset_linestarts:
                    line_start = jset_linestart[:-2] + str(index) + jset_linestart[-1]
                    if jset_linestart == 'ImpOptionPanel.impuritySelect[]':
                        new_content = '1'
                    elif jset_linestart == 'ImpOptionPanel.impurityMass[]':
                        new_content = str(imp_data[index][1])
                    elif jset_linestart == 'ImpOptionPanel.impurityCharge[]':
                        new_content = str(imp_data[index][2])
                    elif jset_linestart == 'ImpOptionPanel.impuritySuperStates[]':
                        new_content = str(imp_data[index][3])

                    modify_jset_line(self.baserun_name, line_start, new_content)

            else:
                line_start = 'ImpOptionPanel.impuritySelect[' + str(index) + ']'
                new_content = 'false'
                modify_jset_line(self.baserun_name, line_start, new_content)

        modify_llcmd(self.baserun_name, self.generator_name, self.generator_username)
    
    def create_sensitivities(self):
    
        '''
    
        Sets up and runs the simulations created by setup_input_sensitivities(). Runs are expected to be numbered as run###something
    
        '''
    
        baserun_number = int(self.baserun_name[3:6])
    
        if not self.force_run:
            for index in range(1,len(self.tag_list),1):
                data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, self.db, self.shot, self.run_output+index, user_name=self.username)
                op = data_entry.open()
    
                if op[0]==0:
                    print('one of the data entries already exists, aborting')
                    exit()
    
                data_entry.close()
    
        number_list = range(baserun_number+1,baserun_number+len(self.tag_list)+1,1)
        number_list = [str(i) for i in number_list]
        ids_list = range(self.run_start+1,self.run_start+len(self.tag_list)+1,1)
        ids_list = [str(i) for i in ids_list]
        ids_output_list = range(self.run_output+1,self.run_output+len(self.tag_list)+1,1)
        ids_output_list = [str(i) for i in ids_output_list]
    
        os.chdir(self.path)
    
        sensitivity_names_list = []

        for number, tag in zip(number_list, self.tag_list):
            sensitivity_names_list.append(self.baserun_name[:3] + number + self.baserun_name[6:] + tag)
    
        for sensitivity_name in sensitivity_names_list:
            shutil.copytree(self.baserun_name, sensitivity_name)
    
        for sensitivity_name, ids_number, ids_output_number in zip(sensitivity_names_list, ids_list, ids_output_list):
            os.chdir(self.path)
    
            b0, r0, start_time, end_time = self.get_r0_b0()

            self.modify_jset(self.path, sensitivity_name, ids_number, ids_output_number, b0, r0)
            modify_llcmd(sensitivity_name, self.baserun_name, self.generator_username)
    
    def run_baserun(self):
    
        os.chdir(self.path + self.baserun_name)
        print('running ' + self.baserun_name)
        os.system('sbatch ./.llcmd')
    
    
    def run_sensitivities(self):
    
        '''
    
        It assumes that the inputs for the sensitivities and the run folders already exists, and runs them.
    
        '''
    
        baserun_number = int(self.baserun_name[3:6])
    
        # If force run is true it will overwrite whaterver is in the target runs. You might lose the output from previous simulations.
    
        if not self.force_run:
            for index in range(1,len(self.tag_list),1):
                data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, self.db, self.shot, self.run_output+index, user_name=self.username)
                op = data_entry.open()
    
                if op[0]==0:
                    print('one of the data entries already exists, aborting')
                    exit()
    
                data_entry.close()
    
        number_list = range(baserun_number+1,baserun_number+len(self.tag_list)+1,1)
        number_list = [str(i) for i in number_list]

        sensitivity_names_list = []

        for number, tag in zip(number_list, self.tag_list):
            sensitivity_names_list.append(self.baserun_name[:3] + number + self.baserun_name[6:] + tag)
    
        os.chdir(self.path)
    
        for sensitivity_name in sensitivity_names_list:
            os.chdir(self.path + '/' + sensitivity_name)
            print('running ' + sensitivity_name)
            os.system('sbatch ./.llcmd')


    def get_r0_b0(self):

        # -------------------- GET b0 and r0 ---------------------
        # Only extract once. This takes time so it's only for speed purposes

        if not self.core_profiles:
            self.core_profiles = open_and_get_core_profiles(self.db, self.shot, self.run_input)
        if not self.equilibrium:
            self.equilibrium = open_and_get_equilibrium(self.db, self.shot, self.run_input)

        # Here I can set the initial time as the time where I can find the first measurement in core profiles or equilibrium

        time_eq = self.equilibrium.time
        time_cp = self.core_profiles.time

        if self.time_start == 0:
            start_time = max(min(time_eq), min(time_cp))
        else:
            start_time = self.time_start

        if self.time_end == 100:
            end_time = min(max(time_eq), max(time_cp))
        else:
            end_time = self.time_end

        index_start = np.abs(time_eq - start_time).argmin(0)
        index_end = np.abs(time_eq - end_time).argmin(0)

        if index_start != index_end:
            b0 = np.average(self.equilibrium.vacuum_toroidal_field.b0[index_start:index_end])
        else:
            b0 = self.equilibrium.vacuum_toroidal_field.b0[0]

        r0 = self.equilibrium.vacuum_toroidal_field.r0*100

# -----------------------------------------------------

        return b0, r0, start_time, end_time

    
    def setup_jetto_simulation(self):
    
        '''
    
        Uses the jetto_tools to setup various parameters for the jetto simulation.
        Updates the magnetic field and the radius. Can be used to update the output and the and the impurity composition.
        Updates the jetto starting time as the first time for which data are available both for the
        equilibrium and the core profiles. Strongly advised!
    
        '''
    
        # In the future an option to operate with the correct ip sign could be added here. Not currently working
        # Also, IBTSIGN seems not to be in the list as it should. not sure what is happening...
    
        #lookup = jetto_tools.lookup.from_file(self.path + '/lookup_json/lookup.json')
        #jset = jetto_tools.jset.read(self.path_generator + '/jetto.jset')
        #namelist = jetto_tools.namelist.read(self.path_generator + '/jetto.in')

        b0, r0, start_time, end_time = self.get_r0_b0()

        if not self.core_profiles:
            self.core_profiles = open_and_get_core_profiles(self.db, self.shot, self.run_input)
        if not self.equilibrium:
            self.equilibrium = open_and_get_equilibrium(self.db, self.shot, self.run_input)

        if not os.path.exists(self.path_baserun):
            shutil.copytree(self.path_generator, self.path_baserun)
        else:
            shutil.copyfile(self.path + '/lookup_json/lookup.json', self.path_baserun + '/lookup.json')  # Just this line should be fine
#            shutil.copyfile(self.path_generator + '/jetto.in', self.path_baserun + '/jetto.in')

        # Changing the orientation when necessary
        # Add IBTSING if ip sign and b0 sign are opposite. There is still a bug.

        extranamelist = get_extraname_fields(self.path_baserun)
        if 'interpretive' not in self.path_generator:
            add_item_lookup('btin', 'EquilEscoRefPanel.BField.ConstValue', 'NLIST1', 'real', 'scalar', self.path_baserun)
            add_item_lookup('rmj', 'EquilEscoRefPanel.refMajorRadius', 'NLIST1', 'real', 'scalar', self.path_baserun)
            add_item_lookup('ibtsign', 'null', 'NLIST1', 'int', 'scalar', self.path_baserun)

            if (b0 > 0 and self.equilibrium.time_slice[0].global_quantities.ip < 0) or (b0 < 0 and self.equilibrium.time_slice[0].global_quantities.ip > 0):
                extranamelist = add_extraname_fields(extranamelist, 'IBTSIGN', ['1'])
            else:
                extranamelist = add_extraname_fields(extranamelist, 'IBTSIGN', ['-1'])

        put_extraname_fields(self.path_baserun, extranamelist)

        template = jetto_tools.template.from_directory(self.path_baserun)
        config = jetto_tools.config.RunConfig(template)

        if 'interpretive' not in self.path_generator:
            if (b0 > 0 and self.equilibrium.time_slice[0].global_quantities.ip < 0) or (b0 < 0 and self.equilibrium.time_slice[0].global_quantities.ip > 0):
                config['ibtsign'] = 1
            else:
                config['ibtsign'] = -1

        if 'interpretive' not in self.path_generator:
            config['btin'] = abs(b0)
            # Absolute value should not be needed anymore since the fix on the ip sign
            #config['btin'] = b0
            config['rmj'] = r0

        if self.esco_timesteps:
            config.esco_timesteps = self.esco_timesteps
        if self.output_timesteps:
            config.profile_timesteps = self.output_timesteps
            config['ntint'] = self.output_timesteps


        config.start_time = start_time
        config.end_time = end_time

        # I could introduce a way not to do this if there are no impurities. Need to add impurities if not there, modifying the various files. Maybe in the future. For now I modify the jset anyway so this part does nothing...
   
        config['atmi'] = 6.0
        config['nzeq'] = 12.0
        config['zipi'] = 6

        # Should automatically run the simulation. Not working for the gateway currently...
        #manager = jetto_tools.job.JobManager()
        #manager.submit_job_to_batch(config, path + baserun_name, run=False)

        config.export(self.path_baserun + 'tmp')
        shutil.copyfile(self.path_baserun + 'tmp' + '/jetto.jset', self.path_baserun + '/jetto.jset')
        #shutil.copyfile(self.path_baserun + 'tmp' + '/jetto.in', self.path_baserun + '/jetto.in')
        shutil.rmtree(self.path_baserun + 'tmp')

    def increase_processors(self, processors = 8, walltime = 24):

        binary, userid = 'v210921_gateway_imas', 'g2fkoech'

        template = jetto_tools.template.from_directory(self.path_baserun)
        config = jetto_tools.config.RunConfig(template)

        config.binary = binary
        config.userid = userid
        config.processors = processors
        config.walltime = walltime

    def get_feedback_on_density_quantities(self):

        # Could add a check if run_exp exists. Should become the runinput though...

        #summary = open_and_get_summary(self.db, self.shot, self.run_exp)
        #self.summary_time = summary.time
        #self.line_ave_density = summary.line_average.n_e.value

        summary = open_and_get_pulse_schedule(self.db, self.shot, self.run_exp)
        self.dens_feedback_time = pulse_schedule.time
        self.line_ave_density = pulse_schedule.density_control.n_e_line.reference.data


    def setup_feedback_on_density(self, run_interpretive):
        '''
    
        Still deciding what exactly this will be. Some step to setup a run with automatic density feedback control
        Strategy should be: add this when setting up the correponding baserun.
    
        '''

        # This might still be useful if trying to use this function standalone, but confusion now   
        #if not os.path.exists(self.path_baserun):
        #    shutil.copytree(self.path_generator, self.path_baserun)
        #else:
        #    shutil.copyfile(self.path_generator + '/lookup.json', self.path_baserun + '/lookup.json')
    
        add_item_lookup('dneflfb', 'null', 'NLIST4', 'real', 'vector', self.path_baserun)
        add_item_lookup('dtneflfb', 'null', 'NLIST4', 'real', 'vector', self.path_baserun)

        dneflfb_strs = []
        for density in self.line_ave_density*1e-6:
            dneflfb_strs.append(str(density))

        dtneflfb_strs = []
        for time in self.dens_feedback_time:
            dtneflfb_strs.append(str(time))

        extranamelist = get_extraname_fields(self.path_baserun)
        extranamelist = add_extraname_fields(extranamelist, 'DNEFLFB', dneflfb_strs)
        extranamelist = add_extraname_fields(extranamelist, 'DTNEFLFB', dtneflfb_strs)
        put_extraname_fields(self.path_baserun, extranamelist)

        template = jetto_tools.template.from_directory(self.path_baserun)
        config = jetto_tools.config.RunConfig(template)

        config['dneflfb'] = self.line_ave_density*1e-6
        config['dtneflfb'] = self.dens_feedback_time
    
        # ------- Can use to create the baseruns when I understand how to create a template from a run without the lookup file (probably just creating the lookup file there)
    
        config.export(self.path_baserun + 'tmp')
        shutil.copyfile(self.path_baserun + 'tmp' + '/jetto.jset', self.path_baserun + '/jetto.jset')
        shutil.rmtree(self.path_baserun + 'tmp')
    
        # ------- Not working yet, jetto_tool automatically setup a slurm environment -------
    
        #    manager = jetto_tools.job.JobManager()
        #    manager.submit_job_to_batch(config, baserun_name + 'tmp', run=False)
    
        # ------- Substitute this to the custom automatic run when available --------
    


    def modify_jset(self, path, sensitivity_name, ids_number, ids_output_number, b0, r0):
    
        '''
    
        Modifies the jset file to accomodate a new run name, username, shot and run. Database not really implemented yet
    
        '''
    
        # Might want more flexibility with the run list here. Maybe set more options in the future
        # The last values with the final times should be handled within the config, but are not. They should be temporary

        line_start_list = [
            'Creation Name', 
            'JobProcessingPanel.runDirNumber', 
            'SetUpPanel.idsIMASDBRunid', 
            'JobProcessingPanel.idsRunid', 
            'AdvancedPanel.catMachID', 
            'AdvancedPanel.catMachID_R', 
            'SetUpPanel.idsIMASDBMachine',
            'SetUpPanel.machine',
            'SetUpPanel.idsIMASDBUser',
            'AdvancedPanel.catOwner', 
            'AdvancedPanel.catOwner_R', 
            'AdvancedPanel.catShotID', 
            'AdvancedPanel.catShotID_R',
            'SetUpPanel.idsIMASDBShot', 
            'SetUpPanel.shotNum',
            'SetUpPanel.endTime',
            'EquilEscoRefPanel.tvalue.tinterval.endRange',
            'EquilIdsRefPanel.rangeEnd',
            'OutputStdPanel.profileRangeEnd',
            'SetUpPanel.startTime',
            'EquilEscoRefPanel.tvalue.tinterval.startRange',
            'EquilIdsRefPanel.rangeStart',
            'OutputStdPanel.profileRangeStart',
            'EquilEscoRefPanel.BField.ConstValue',
            'EquilEscoRefPanel.BField ',
            'EquilEscoRefPanel.refMajorRadius'
        ]
    
        new_content_list = [
            path + sensitivity_name + '/jetto.jset', 
            sensitivity_name[3:], 
            str(ids_number), 
            str(ids_output_number), 
            self.db, 
            self.db,
            self.db,
            self.db, 
            self.username,
            self.username, 
            self.username, 
            str(self.shot), 
            str(self.shot), 
            str(self.shot), 
            str(self.shot),
            str(self.time_end),
            str(self.time_end),
            str(self.time_end),
            str(self.time_end),
            str(self.time_start),
            str(self.time_start),
            str(self.time_start),
            str(self.time_start),
            str(b0),
            str(b0),
            str(r0)
        ]
    
        # ImpOptionPanel.impuritySelect[1]                            : false to deselect the impurity
    
        for line_start, new_content in zip(line_start_list, new_content_list):
            modify_jset_line(sensitivity_name, line_start, new_content)
    
    def modify_jetto_in(self, sensitivity_name, r0, b0, time_start, time_end, num_times_print = None, num_times_eq = None, imp_datas_ids = [[1.0, 12.0, 6, 6.0]], ibtsign = 1, interpretive_flag = False):

        '''
    
        modifies the jset file to accomodate a new run name. Default impurity is carbon
    
        '''

        imp_datas = []
        for index in range(7):
            imp_datas.append([0.0, 0.0, 0, 0.0])

        for index, imp_data in enumerate(imp_datas_ids):
            imp_datas[index] = imp_data

        imp_density, imp_mass, imp_super, imp_charge = '', '', '', ''

        for index in range(7):
            imp_density += str(imp_datas[index][0]) + '      ,  '
            imp_mass += str(imp_datas[index][1]) + '      ,  '
            imp_super += str(imp_datas[index][2]) + '      ,  '
            imp_charge += str(imp_datas[index][3]) + '      ,  '

        read_data = []
    
        with open(sensitivity_name + '/' + 'jetto.in') as f:
            lines = f.readlines()
            for line in lines:
                read_data.append(line)
    
        # Could also use a list here as well, but just trying now
        index_btin, index_nlist1, index_nlist4 = 0, 0, 0

        original_num_tprint = 1

        for index, line in enumerate(read_data):
            if line.startswith('  NTINT'):
                original_num_tprint = int(re.search(r'\d+', line).group())

        jetto_in_nameslist = {
            '  RMJ': str(r0),
            '  BTIN': str(b0),
            '  TBEG': str(time_start),
            '  TMAX': str(time_end),
            '  MACHID': '\'' + self.db + '\'',
            '  NPULSE': str(self.shot),
            '  NIMP': str(len(imp_datas_ids))
            #'  NIMP': '1'  # Needs to be changed
        }

        if num_times_print != None:
           jetto_in_nameslist['  NTINT'] = str(num_times_print)
           jetto_in_nameslist['  NTPR'] = str(num_times_print - 2)

        if interpretive_flag:
           del jetto_in_nameslist['  RMJ']
           del jetto_in_nameslist['  BTIN']

        for index, line in enumerate(read_data):
            if line[:6] == '  BTIN':
                index_btin = index
            elif line[:18] == ' Namelist : NLIST4':
                index_nlist4 = index
            elif line[:8] == ' &NLIST1':
                index_nlist1 = index

        for index, line in enumerate(read_data):
            for jetto_name in jetto_in_nameslist:
                if line.startswith(jetto_name):
                    read_data[index] = read_data[index][:14] + jetto_in_nameslist[jetto_name] + '    ,'  + '\n'

            # needs to be modified
            if line[:8] == '  TIMEQU':
                if num_times_eq:
                    read_data[index] = read_data[index][:14] + str(time_start) + ' , ' + str(time_end) + ' , '
                    # Testing, do not leave like this
                    #read_data[index] += str(num_times_eq) + ' , ' + '\n'
                    read_data[index] += str((time_end - time_start)/num_times_eq) + ' , ' + '\n'
                else:
                    original_time_eq = re.findall("\d+\.\d+", line)
                    if len(original_time_eq) == 1:
                        num_times_eq = 1
                    else:
                        num_times_eq = int(round((float(original_time_eq[1]) - float(original_time_eq[0]))/float(original_time_eq[-1])))
                        # The meaning of the numbers is different when interpretive equilibrium. Trying to handle that here.
                        if num_times_eq == 0:
                            num_times_eq = int(round(float(original_time_eq[-1])))
                    read_data[index] = read_data[index][:14] + str(time_start) + ' , ' + str(time_end) + ' , '
                    # Testing, do not leave like this
                    read_data[index] += str((time_end - time_start)/num_times_eq) + ' , ' + '\n'
                    #read_data[index] += str(num_times_eq) + ' , ' + '\n'

        # Nexessary for interpretive runs when there is no btin
        if index_btin == 0:
            index_btin = index_nlist1 + 2
            read_data.insert(index_btin, '  RMJ   =  ' + str(r0) + '     ,'  + '\n')
            read_data.insert(index_btin, '  BTIN  =  ' + str(b0) + '     ,'  + '\n')

        #if not interpretive_flag:
        #    if ibtsign == 1:
        #        read_data.insert(index_btin, '  IBTSIGN  =  1        ,'  + '\n')
        #    elif ibtsign == -1 :
        #        read_data.insert(index_btin, '  IBTSIGN  =  -1       ,'  + '\n')
         
        if ibtsign == 1:
            read_data.insert(index_btin, '  IBTSIGN  =  1        ,'  + '\n')
        elif ibtsign == -1 :
            read_data.insert(index_btin, '  IBTSIGN  =  -1       ,'  + '\n')


        if self.line_ave_density is not None:
            # -------------- Feedback density density -----------------
            dneflfb_lines = []
            for index_dens, dens_value in enumerate(self.line_ave_density):
                dneflfb_line = '  DNEFLFB' + '(' + str(index_dens+1) + ')' + ' =  ' + str(dens_value) + '    , \n'
                dneflfb_lines.append(dneflfb_line)

            read_data.insert(index_nlist4+10, dneflfb_lines)
    
            # -------------- Feedback density time --------------------

            dtneflfb_lines = []
            for index_time, time_value in enumerate(self.summary_time):
                dtneflfb_line = '  DTNEFLFB' + '(' + str(index_time+1) + ')' + ' =  ' + str(time_value) + '    , \n'
                dtneflfb_lines.append(dtneflfb_line)

            read_data.insert(index_nlist4+12, dtneflfb_lines)

        # Need to extract the previous TPRINT and adapt the array to the new start time-end time
        if not num_times_print:
            num_times_print = original_num_tprint

        tprint_start = 0
        for index, line in enumerate(read_data):
            if line[:8] == '  TPRINT':
                tprint_start = index
                tprint = ''
                for index_print in range(num_times_print):
                    new_time = time_start + (time_end - time_start)/num_times_print*index_print
                    tprint = tprint + str(new_time) + ' , '
                read_data[index] = read_data[index][:14] + tprint + '\n'
            if line[:6] == '      ' and tprint_start != 0 and index > tprint_start and index < tprint_start +10:
                read_data[index] = '             ' + '\n'


        # Could simplify   
        # ALFP, ALFINW might need to be modified as well

        jetto_in_multiline_nameslist = {
            '  ALFI': imp_density,
            '  ATMI': imp_mass,
            '  NZEQ': imp_super,
            '  ZIPI': imp_charge,
        }

        def change_jetto_in_multiline(item):
            print_start = 0
            for index, line in enumerate(read_data):
                if line.startswith(item[0]):
                    print_start = index
                    read_data[index] = read_data[index][:14] + item[1]  + '\n'
                if line[:6] == '      ' and print_start != 0 and index == print_start + 1:
                    del read_data[index]
        
        # for item in jetto_in_multiline_nameslist:
        # change_jetto_in_multiline(item)


        print_start = 0
        for index, line in enumerate(read_data):
            if line[:6] == '  ALFI':
                print_start = index
                read_data[index] = read_data[index][:14] + imp_density  + '\n'
            if line[:6] == '      ' and print_start != 0 and index == print_start + 1:
                del read_data[index]
    
        print_start = 0
        for index, line in enumerate(read_data):
            if line[:6] == '  ATMI':
                print_start = index
                read_data[index] = read_data[index][:14] + imp_mass  + '\n'
            if line[:6] == '      ' and print_start != 0 and index == print_start + 1:
                del read_data[index]
    
        print_start = 0
        for index, line in enumerate(read_data):
            if line[:6] == '  NZEQ':
                print_start = index
                read_data[index] = read_data[index][:14] + imp_super  + '\n'
            if line[:6] == '      ' and print_start != 0 and index == print_start + 1:
                read_data[index] = '             ' + '\n'
    
        print_start = 0
        for index, line in enumerate(read_data):
            if line[:6] == '  ZIPI':
                print_start = index
                read_data[index] = read_data[index][:14] + imp_charge  + '\n'
            if line[:6] == '      ' and print_start != 0 and index == print_start + 1:
                read_data[index] = '             ' + '\n'
    
        with open(sensitivity_name + '/' + 'jetto.in', 'w') as f:
            for line in read_data:
                f.writelines(line)

def get_extraname_fields(path):

    '''

    Gets all the extranamelist fields in the jset file. This is necessary to put it there when it is not already there, ready to be modified by the jetto tools.

    '''

    read_lines = []

    with open(path + '/' + 'jetto.jset') as f:
        lines = f.readlines()
        for line in lines:
            read_lines.append(line)

    extranamelist_lines = []
    for line in read_lines:
        if line.startswith('OutputExtraNamelist.selItems.cell'):
            extranamelist_lines.append(line)

    indexs1, indexs2, values = [], [], []
    for line in extranamelist_lines:
        indexs1.append(int(line.split('[')[1].split(']')[0]))
        indexs2.append(int(line.split('[')[2].split(']')[0]))
        values.append(line[62:-1])

    # The following assumes that the elements in the extranamelist are alway in order 0-1-2

    extranamelist = {}
    array_flag = False
    for index1, index2, value in zip(indexs1, indexs2, values):
        if index2 == 0:
            key = value
            extranamelist[key] = []

        if index2 == 1:
            if value != '':
                array_flag = True
            else:
                array_flag = False

        if index2 == 2:
            if array_flag:
                extranamelist[key].append(value)
            else:
                extranamelist[key] = [value]

    return extranamelist

def add_extraname_fields(extranamelist, key, values):

    # Values needs to be an array of strings

    extranamelist[key] = values
    extranamelist_ordered = {key: value for key, value in sorted(extranamelist.items())}

    return extranamelist_ordered

def put_extraname_fields(path, extranamelist):

    index_start = 0
    namelist_start = 'OutputExtraNamelist.selItems.cell'

    read_lines = []
    with open(path + '/' + 'jetto.jset') as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            if line.startswith('NeutralSourcePanel'):
                index_start = index
            if not line.startswith(namelist_start):
                read_lines.append(line)

    index_start += 1

    extranamelist_lines = []
    ilist = 0
    for index_item, item in enumerate(extranamelist.items()):
        for ielement, element in enumerate(item[1]):
            new_line1 = namelist_start + '[' + str(ilist) + ']' + '[' + str(0) + ']'
            new_line2 = namelist_start + '[' + str(ilist) + ']' + '[' + str(1) + ']'
            new_line3 = namelist_start + '[' + str(ilist) + ']' + '[' + str(2) + ']'

            spaces = ' '*(60 - len(new_line1))

            new_line1 = new_line1 + spaces + ': ' + item[0] + '\n'
            if len(item[1]) == 1:
                new_line2 = new_line2 + spaces + ': \n'
            else:
                new_line2 = new_line2 + spaces + ': ' + str(ielement+1) + '\n'
            new_line3 = new_line3 + spaces + ': ' + element + '\n'

            extranamelist_lines.append(new_line1)
            extranamelist_lines.append(new_line2)
            extranamelist_lines.append(new_line3)

            ilist += 1

    read_lines.insert(index_start, extranamelist_lines)


    with open(path + '/' + 'jetto.jset', 'w') as f:
        for line in read_lines:
            f.writelines(line)

    modify_jset_line(path, 'OutputExtraNamelist.selItems.rows', str(ilist))
    

#  This function is just for testing, can be deleted later
def get_put_namelist(path):

    # the extranamelist might be updated even without the extra.. = something

    extranamelist = get_extraname_fields(path)
    extranamelist = add_extraname_fields(extranamelist, 'IBTSIGN', ['1'])
    extranamelist = add_extraname_fields(extranamelist, 'DNEFLFB', ['1e13', '2e13'])
    extranamelist = add_extraname_fields(extranamelist, 'DTNEFLFB', ['1', '2'])
    put_extraname_fields(path, extranamelist)


def modify_jset_line(sensitivity_name, line_start, new_content):

    '''

    Modifies a line of the jset file. Maybe it would be better to change all the lines at once but future work, not really speed limited now

    '''
    read_data = []

    len_line_start = len(line_start)
    with open(sensitivity_name + '/' + 'jetto.jset') as f:
        lines = f.readlines()
        for line in lines:
            read_data.append(line)

        for index, line in enumerate(read_data):
            if line[:len_line_start] == line_start:
                read_data[index] = read_data[index][:62] + new_content + '\n'

    with open(sensitivity_name + '/' + 'jetto.jset', 'w') as f:
        for line in read_data:
            f.writelines(line)


def modify_llcmd(sensitivity_name, baserun_name, generator_username):

    '''

    modifies the jset file to accomodate a new run name

    '''

    read_data = []
    username = username = getpass.getuser()

    with open(sensitivity_name + '/' + '.llcmd') as f:
        lines = f.readlines()
        for line in lines:
            read_data.append(line)

        for index, line in enumerate(read_data):
            read_data[index] = line.replace(baserun_name, sensitivity_name)
            if generator_username:
#                print('changing' + generator_username + 'in' + username)
                read_data[index] = read_data[index].replace(generator_username, username)


    with open(sensitivity_name + '/' + '.llcmd', 'w') as f:
        for line in read_data:
            f.writelines(line)

def add_item_lookup(name, name_jset, namelist, name_type, name_dim, path):

    read_data = []

    with open(path + '/' + 'lookup.json') as f:
        lines = f.readlines()
        for line in lines:
            read_data.append(line)

    new_item = []

    new_item.append(' \"' + name + '\": { \n')
    if name_jset == 'null':
        new_item.append('  \"jset_id\": ' + name_jset + ',\n')
    else:
        new_item.append('  \"jset_id\": \"' + name_jset + '\",\n')
    new_item.append('  \"nml_id\": { \n')
    new_item.append('   \"namelist\": \"' + namelist + '\",\n')
    new_item.append('   \"field\":  \"' + name.upper() + '\" \n')
    new_item.append('  }, \n')
    new_item.append('  \"type\": \"' + name_type + '\",\n')
    new_item.append('  \"dimension\": \"' + name_dim + '\" \n')
    new_item.append(' }, \n')

    read_data.insert(1, new_item)

    with open(path + '/' + 'lookup.json', 'w') as f:
        for line in read_data:
            f.writelines(line)

# Redefined for when prepare_im_input is not imported
def open_and_get_core_profiles(db, shot, run, username = ''):

    if username == '':
        data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run, user_name=username)

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

def open_and_get_equilibrium(db, shot, run, username = ''):

    if username == '':
        data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run, user_name=username)

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

def open_and_get_pulse_schedule(db, shot, run, username = ''):

    if username == '':
        data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run, user_name=getpass.getuser())
    else:
        data_entry = imas.DBEntry(imasdef.MDSPLUS_BACKEND, db, shot, run, user_name=username)

    op = data_entry.open()

    if op[0]<0:
        cp=data_entry.create()
        print(cp[0])
        if cp[0]==0:
            print("data entry created")
    elif op[0]==0:
        print("data entry opened")

    pulse_schedule = data_entry.get('pulse_schedule')
    data_entry.close()

    return(pulse_schedule)


if __name__ == "__main__":

    print('main, not supported, use commands')
