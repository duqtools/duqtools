#!/usr/bin/env python
import os
import sys
import re
import copy
import numpy as np
from scipy.interpolate import interp1d
#import matplotlib
#matplotlib.use('Qt5Agg')
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython import display
import argparse

import imas

allowed_ids_list = [
    'summary',
    'equilibrium',
    'core_profiles',
    'core_sources',
    'core_transport'
]

keys_list = {
    'time_trace': [],
    'profiles_1d': [],
    'profiles_2d': []
}

keys_list['profiles_1d'] = [
    'core_profiles.profiles_1d[].q', 
    'core_profiles.profiles_1d[].electrons.density_thermal',
    'core_profiles.profiles_1d[].electrons.density',
    'core_profiles.profiles_1d[].electrons.density_fit.measured',
    'core_profiles.profiles_1d[].electrons.density_fit.measured_error_upper',
    'core_profiles.profiles_1d[].electrons.temperature',
    'core_profiles.profiles_1d[].electrons.temperature_fit.measured',
    'core_profiles.profiles_1d[].electrons.temperature_fit.measured_error_upper',
    'core_profiles.profiles_1d[].t_i_average',
    'core_profiles.profiles_1d[].t_i_average_fit.measured',
    'core_profiles.profiles_1d[].t_i_average_fit.measured_error_upper',
    'core_profiles.profiles_1d[].ion[0].temperature',
    'core_profiles.profiles_1d[].ion[0].temperature_fit.measured',
    'core_profiles.profiles_1d[].ion[0].temperature_fit.measured_error_upper',
    'core_profiles.profiles_1d[].ion[0].density',
    'core_profiles.profiles_1d[].ion[1].temperature',
    'core_profiles.profiles_1d[].ion[1].temperature_fit.measured',
    'core_profiles.profiles_1d[].ion[1].temperature_fit.measured_error_upper',
    'core_profiles.profiles_1d[].ion[1].density',
    'core_profiles.profiles_1d[].ion[1].density_fit.measured',
    'core_profiles.profiles_1d[].ion[1].density_fit.measured_error_upper',
    'core_profiles.profiles_1d[].t_i_average', 
    'core_profiles.profiles_1d[].zeff',
    'core_profiles.profiles_1d[].grid.rho_tor_norm',
    'equilibrium.time_slice[].profiles_1d.psi',
    'equilibrium.time_slice[].profiles_1d.f', 
    'equilibrium.time_slice[].profiles_1d.q', 
    'equilibrium.time_slice[].profiles_1d.pressure', 
    'equilibrium.time_slice[].profiles_1d.rho_tor_norm', 
    'equilibrium.time_slice[].boundary.outline.r', 
    'equilibrium.time_slice[].boundary.outline.z', 
    'equilibrium.time_slice[].profiles_2d[].grid.dim1', 
    'equilibrium.time_slice[].profiles_2d[].grid.dim2',
    'core_sources.source[].profiles_1d[].electrons.energy', 
    'core_sources.source[].profiles_1d[].total_ion_energy', 
    'core_sources.source[].profiles_1d[].j_parallel', 
    'core_sources.source[].profiles_1d[].momentum_tor', 
    'core_sources.source[].profiles_1d[].ion[].particles', 
    'core_sources.source[].profiles_1d[].grid.rho_tor_norm',
]

keys_list['time_trace'] = [
    'core_profiles.global_quantities.ip', 
    'core_profiles.global_quantities.v_loop', 
    'core_profiles.global_quantities.li_3', 
    'core_profiles.global_quantities.energy_diamagnetic',
    'summary.global_quantities.ip.value', 
    'summary.heating_current_drive.power_nbi.value', 
    'summary.heating_current_drive.power_ic.value', 
    'summary.heating_current_drive.power_ec.value', 
    'summary.heating_current_drive.power_lh.value', 
    'summary.stationary_phase_flag.value',
    'summary.global_quantities.v_loop.value', 
    'summary.global_quantities.li.value', 
    'summary.global_quantities.li_mhd.value', 
    'summary.global_quantities.energy_diamagnetic.value', 
    'summary.global_quantities.energy_mhd.value', 
    'summary.global_quantities.energy_thermal.value', 
    'summary.global_quantities.beta_pol.value', 
    'summary.global_quantities.beta_pol_mhd.value', 
    'summary.global_quantities.beta_tor_norm.value', 
    'summary.global_quantities.beta_tor.value', 
    'summary.global_quantities.power_radiated.value', 
    'summary.fusion.neutron_fluxes.total.value',
    'equilibrium.time_slice[].global_quantities.ip', 
    'equilibrium.time_slice[].global_quantities.li_3', 
    'equilibrium.time_slice[].global_quantities.beta_pol', 
    'equilibrium.time_slice[].global_quantities.beta_tor', 
    'equilibrium.time_slice[].global_quantities.magnetic_axis.r', 
    'equilibrium.time_slice[].global_quantities.magnetic_axis.z'
]

keys_list['profiles_2d'] = [
    'equilibrium.time_slice[].profiles_2d[].psi'
]

keys_list['errors'] = {
    'time_trace': [],
    'profiles_1d': [],
    'profiles_2d': []
}

keys_list['errors']['time_trace'] = [
    'absolute_error'
]

keys_list['errors']['profiles_1d'] = [
    'average_absolute_error'
]

# Add more here as they are needed.
operations = [
    '*2',
    '/2',
    '+',
    '-',
    '*',
    '/'
]

def expand_error_keys(category=None):
    error_keys = []
    if category in keys_list and category in keys_list['errors']:
        for var in keys_list[category]:
            for err in keys_list['errors'][category]:
                error_keys.append(var+'.'+key)
    return error_keys

def input():

    parser = argparse.ArgumentParser(
        description=
"""Compare validation metrics from HFPS input / output IDSs. Preliminary version, adapted from scripts from D. Yadykin and M. Marin.\n
---
Examples:\n
python compare_im_runs.py -u g2aho -d jet -s 94875 -r 1 102 --time_begin 48 --time_end 49 --steady_state -sig 'core_profiles.profiles_1d[].q' 'summary.global_quantities.li.value'\n
---
""", 
    epilog="", 
    formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("--backend",  "-b",              type=str,   default="mdsplus", choices=["mdsplus", "hdf5"], help="Backend with which to access data")
    parser.add_argument("--database", "-d",   nargs='+', type=str,   default=None,                                   help="Database/machine name(s) in which the data is stored")
    parser.add_argument("--shot",     "-s",   nargs='+', type=int,   default=None,                                   help="Shot number(s) in which the data is stored")
    parser.add_argument("--run",      "-r",   nargs='+', type=int,   default=None,                                   help="Run number(s) in which the data is stored")
    parser.add_argument("--user",     "-u",   nargs='*', type=str,   default=[os.getenv("USER")],                    help="Username(s) with the data in his/her imasdb")
    parser.add_argument("--version",  "-v",              type=str,   default="3",                                    help="UAL version")
    parser.add_argument("--time_begin",                  type=float, default=None,                                   help="Slice shot file beginning at time (s)")
    parser.add_argument("--time_end",                    type=float, default=None,                                   help="Slice shot file ending at time (s)")
    parser.add_argument("--time_out",         nargs='*', type=float, default=None,                                   help="Slice output interpolated to times (s), automatically toggles uniform")
    parser.add_argument("--signal",   "-sig", nargs='+', type=str,   default=None,                                   help="Full IDS signal names to be compared")
    parser.add_argument("--source",           nargs='*', type=str,   default=['total'],                              help="sourceid to be plotted(nbi, ec,etc as given in dd description), make sence if core_source is given as target ids, default is total")
    parser.add_argument("--transport",        nargs='*', type=str,   default=['transport_solver'],                   help="transpid to be plotted(neoclassical, anomalous, ets, cherck dd for more entires), make sence if core_transport is given as target ids, default is transport_solver")
    parser.add_argument("--steady_state",                            default=False, action='store_true',             help="Flag to identify that the input is a single point")
    parser.add_argument("--save_plot",                               default=False, action='store_true',             help="Toggle saving of plot into default file names")
    parser.add_argument("--uniform",                                 default=False, action='store_true',             help="Toggle interpolation to uniform time and radial basis, uses first run as basis unless steady state flag is on")
#    parser.add_argument("--analyze_traces",   nargs='*', type=str,   default=None, choices=["absolute_error"],       help="Define which analyses to perform after time trace comparison plots")
#    parser.add_argument("--analyze_profiles", nargs='*', type=str,   default=None, choices=["average_absolute_error"], help="Define which analyses to perform after profile comparison plots")
    parser.add_argument("--analyze",                                 default=False, action='store_true',             help="Toggle extra analysis routines, automatically toggles uniform")
    parser.add_argument("--correct_sign",                            default=None, action='store_true',              help="Allows to change the sign of the output if it is not identical to reference run")
    parser.add_argument("--function", "-func", nargs='*', type=str,  default=None,                                   help="Specify functions of multiple variables")
    parser.add_argument("--calc_only",                               default=False, action='store_true',             help="Toggle off all plotting")

    args=parser.parse_args()

    return args


def getShotFile(ids_name,shot,runid,user,database,backend=imas.imasdef.MDSPLUS_BACKEND):
    print('to be opened',user,database,shot,runid)
    data = None
    ids = imas.DBEntry(backend, database, shot, runid, user)
    ids.open()
    if ids_name in allowed_ids_list:
#        data = ids.get_slice(ids_name, time, imas.imasdef.CLOSEST_SAMPLE, occurrence=0)
        data = ids.get(ids_name)
    else:
        raise TypeError('IDS given is not implemented yet')
    return data

def extend_list(inlist, nmax, default=None):
    outlist = inlist
    while len(outlist) < nmax:
        value = inlist[-1] if len(inlist) > 0 else default
        outlist.append(value)
    return outlist

def get_sourceid(ids, sid):
    nsour=len(ids.source)
    nosid=True
    for isour in range(nsour):
        if ids.source[isour].identifier.name==sid:
            sourceid=isour
            nosid=False
            break
    if nosid:
        raise IOError('no sid with name %s found, check ids used' % (sid))
    return sourceid

def get_transpid(ids, tid):
    nmod=len(ids.model)
    notid=True
    for imod in range(nmod):
        if ids.model[imod].identifier.name==tid:
            transpid=imod
            notid=False
            break
    if notid:
        raise IOError('no tid with name %s found, check ids used' % (tid))
    return transpid

def fit_and_substitute(x_old, x_new, y_old):
    ifunc = interp1d(x_old, y_old, fill_value='extrapolate', bounds_error=False)
    y_new = np.array(ifunc(x_new)).flatten()
    y_new[y_new > 1.0e25] = 0.0    # This is just in case
    return y_new

def get_onesig(ids,signame,time_begin,time_end=None,sid=None,tid=None):
    data_dict = {}
    sigcomp = signame.split('.')
    # IDS name must be the first part of the signal name
    idsname = sigcomp[0]
    if idsname not in allowed_ids_list:
        raise IOError('IDS %s not supported by this tool.' % (idsname))

    # Time vector discovery section here
    tstring = 'ids.time'
    tvec = None
    try:
       tvec = eval(tstring)
       if not isinstance(tvec, np.ndarray):
           tvec = np.array([tvec]).flatten()
    except:
       raise IOError('Time vector not present in IDS')

    # Define indices within the time vector for the user-defined begin and end times
    tb_ind = np.abs(tvec - time_begin).argmin(0)
    te_ind = tb_ind
    if time_end is not None:
         te_ind = np.abs(tvec - time_end).argmin(0)
    if te_ind == tb_ind:
        te_ind = tb_ind + 1

    for tt in np.arange(tb_ind, te_ind):
        xstring = 'none'
        ystring = 'none'
        datatype = 'none'
        sid_ind = -1
        tid_ind = -1
        # Auto-detect 0D, 1D, 2D signals based purely on the name, category lists at top of file
        for key in keys_list:
            if signame in keys_list[key]:
                for ii in range(len(sigcomp)):
                    tstr = sigcomp[ii]
                    mm = re.match(r'^(.+)\[\]$', tstr)
                    # Signal names passed in have empty [] as placeholder for indices, eval function needs a defined index
                    # This section fills in the variable name which holds the index value to be used in eval
                    if mm and mm.group(1):
                        if mm.group(1) == 'time_slice':
                            tstr = 'time_slice[tt]'
                        elif mm.group(1) == 'profiles_1d':
                            tstr = 'profiles_1d[tt]'
                        elif mm.group(1) == 'source':
                            sid_ind = get_sourceid(ids, sid)
#                            print('sourceid',sid,sid_ind)
                            tstr = 'source[sid_ind]'
                        elif mm.group(1) == 'ion':
                            tstr = 'ion[0]'
                        elif mm.group(1) == 'profiles_2d':
                            tstr = 'profiles_2d[0]'
                        else:
                            tid_ind = get_transpid(ids,tid)
#                            print('transpid',tid,tid_ind)
                    sigcomp[ii] = tstr
                ystring = 'ids.' + '.'.join(sigcomp[1:])
                datatype = key
                if datatype == 'time_trace':
                    # Equilibrium IDS is strange
                    if idsname not in ['equilibrium']:
                        ystring += '[tt]'
        # Determine corresponding vectors related to signal data (could be time or radius depending on quantity)
        if idsname == 'summary':
            if datatype == 'time_trace':
                xstring = 'ids.time[tt]'
        if idsname == 'equilibrium':
            if datatype == 'profiles_1d':
                xstring = 'ids.profiles_1d[tt].grid.rho_tor_norm'
            if datatype == 'time_trace':
                xstring = 'ids.time[tt]'
            if datatype == 'profiles_2d':
                raise TypeError("No.")
        if idsname == 'core_profiles':
            if datatype == 'profiles_1d':
                xstring = 'ids.profiles_1d[tt].grid.rho_tor_norm'
            if datatype == 'time_trace':
                xstring = 'ids.time[tt]'
        if idsname == 'core_sources':
            if datatype == 'profiles_1d':
                xstring = 'ids.source[sid_ind].profiles_1d[tt].grid.rho_tor_norm'
            if datatype == 'time_trace':
                xstring = 'ids.time[tt]'
        if idsname == 'core_transport':
            if datatype == 'profiles_1d':
                xstring='ids.model[tid_ind].profiles_1d[tt].grid_d.rho_tor_norm'
        # Defining a different x vector for the experimental data
        if idsname == 'core_profiles' and signame == 'core_profiles.profiles_1d[].electrons.temperature_fit.measured':
            xstring = 'ids.profiles_1d[tt].electrons.temperature_fit.rho_tor_norm'
        if idsname == 'core_profiles' and signame == 'core_profiles.profiles_1d[].electrons.temperature_fit.measured_error_upper':
            xstring = 'ids.profiles_1d[tt].electrons.temperature_fit.rho_tor_norm'

        if idsname == 'core_profiles' and signame == 'core_profiles.profiles_1d[].electrons.density_fit.measured':
            xstring = 'ids.profiles_1d[tt].electrons.density_fit.rho_tor_norm'
        if idsname == 'core_profiles' and signame == 'core_profiles.profiles_1d[].electrons.density_fit.measured_error_upper':
            xstring = 'ids.profiles_1d[tt].electrons.density_fit.rho_tor_norm'

        if idsname == 'core_profiles' and signame == 'core_profiles.profiles_1d[].t_i_average_fit.measured':
            xstring = 'ids.profiles_1d[tt].t_i_average_fit.rho_tor_norm'
        if idsname == 'core_profiles' and signame == 'core_profiles.profiles_1d[].t_i_average_fit.measured_error_upper':
            xstring = 'ids.profiles_1d[tt].t_i_average_fit.rho_tor_norm'

        if idsname == 'core_profiles' and signame == 'core_profiles.profiles_1d[].ion[1].density_fit.measured':
            xstring = 'ids.profiles_1d[tt].ion[1].density_fit.rho_tor_norm'
        if idsname == 'core_profiles' and signame == 'core_profiles.profiles_1d[].ion[1].density_fit.measured_error_upper':
            xstring = 'ids.profiles_1d[tt].ion[1].density_fit.rho_tor_norm'

        # Define x vector (could be time or radius)
        if xstring == 'ids.time[tt]':
            xvec = np.array([tvec[tt]]).flatten()
        else:
            try:
                xvec=eval(xstring)
                if not isinstance(xvec, np.ndarray):
                    xvec = np.array([xvec]).flatten()
            except:
                raise IOError('Radial vector %s not present in IDS.' % (xstring))
        # Define y vector(value of signal)

        try:
            yvec=eval(ystring)
            if not isinstance(yvec, np.ndarray):
                yvec = np.array([yvec]).flatten()
        except:
            raise IOError('Value vector %s not present in IDS.' % (ystring))

        # Check dimension consistency
        if len(yvec) != len(xvec):
            print('dimensions of x,y are not consistent for signal ', ystring,' set y to the same size as x and fill with zeros')
            yvec=np.zeros(len(xvec))

        data_dict[tvec[tt]] = {"x": xvec, "y": yvec}

    return data_dict

def get_onedict(sigvec,user,db,shot,runid,time_begin,time_end=None,sid=None,tid=None,interpolate=False):
    out_data_dict = {}
    ids_dict = {}
    # Split signals based on which IDS they come from, allows efficient IDS reading
    for sig in sigvec:
        sigcomp = sig.split('.')
        if sigcomp[0] not in ids_dict:
            ids_dict[sigcomp[0]] = [sig]
        else:
            ids_dict[sigcomp[0]].append(sig)
    t_fields = []
    xt_fields = []
    # Loop over IDSs, extracted all requested signals from each
    for idsname, siglist in ids_dict.items():
        ids=getShotFile(idsname,shot,runid,user,db)
        for signame in siglist:
            raw_data_dict = get_onesig(ids,signame,time_begin,time_end,sid,tid)
            ytable = None
            new_x = None
            new_t = np.array([])
            for key, val in raw_data_dict.items():
                if val["x"].size > 1:
                    # Allow interpolation to standardize radial vectors within an IDS signal (not usually necessary but could be needed if radial vector changes in time)
                    # Default call of function does not interpolate
                    if interpolate:
                        if new_x is None:
                            new_x = val["x"]
                        new_y = fit_and_substitute(val["x"], new_x, val["y"])
                        ytable = np.vstack((ytable, new_y)) if ytable is not None else np.atleast_2d(new_y)
                    else:
                        if ytable is None:
                            ytable = []
                        ytable.append(val)
                else:
                    ytable = np.hstack((ytable, val["y"])) if ytable is not None else np.array([val["y"]]).flatten()
                # Time of time slice stored as key of raw_data_dict, extract and stack into an actual time vector
                new_t = np.hstack((new_t, key))
            # Store data into container
            out_data_dict[signame] = ytable
            out_data_dict[signame+".t"] = new_t
            if new_x is None:
                t_fields.append(signame)
            else:
                out_data_dict[signame+".x"] = new_x
                xt_fields.append(signame)
    if out_data_dict:
        out_data_dict["time_signals"] = t_fields
        out_data_dict["profile_signals"] = xt_fields
    return out_data_dict

def standardize_manydict(runvec,sigvec,time_begin,time_end=None,time_vector=None,set_reference=None):
    out_dict = {}
    temp_run_dict = {}
    reference_tag = None
    first_tag = None
    # Loop over runs to extract data, set first run as the reference run for time and radial vectors
    for run in runvec:
        user = run[0]
        db = run[1]
        shot = run[2]
        runid = run[3]
        tag = "%s/%s/%d/%d" % (user, db, shot, runid)
        # Adding this line to allow for the flipping of all variables when it's not the first run. Might be necessary for the q profile
        if not first_tag:
            first_tag = tag

        temp_run_dict[tag] = get_onedict(sigvec,user,db,shot,runid,time_begin,time_end,interpolate=True)

        if reference_tag is None:
            reference_tag = tag
    # If another run is required to be the reference, then set that to be the reference if it is present
    if set_reference is not None and set_reference in temp_run_dict:
        reference_tag = set_reference
    ref_dict = {}   # Container for reference run
    # Transform reference data into the required field names and store in reference container
    for key in temp_run_dict[reference_tag]:
        if not key.endswith(".x") and not key.endswith(".t"):
            if key not in ref_dict:
                ref_dict[key] = {}
            if time_vector is None:
                ref_dict[key][reference_tag] = copy.deepcopy(temp_run_dict[reference_tag][key])
                if key+".x" in temp_run_dict[reference_tag]:
                    ref_dict[key+".x"] = copy.deepcopy(temp_run_dict[reference_tag][key+".x"])
                #if key+".t" in run_dict:
                ref_dict[key+".t"] = copy.deepcopy(temp_run_dict[reference_tag][key+".t"])
            else:
                # User-defined time vector takes priority over the time vector inside the user-defined reference run
                ytable = np.atleast_2d(temp_run_dict[reference_tag][key])
                # Radial interpolation will take place in the next loop
                if key+".x" in temp_run_dict[reference_tag]:
                    ref_dict[key+".x"] = copy.deepcopy(temp_run_dict[reference_tag][key+".x"])
                ref_dict[key+".t"] = copy.deepcopy(time_vector)
                # Perform time vector interpolation, always present
                t_new = ref_dict[key+".t"]
                if len(temp_run_dict[reference_tag][key+".t"]) > 1:
                    ytable_new = None
                    for ii in range(ytable.shape[1]):
                        y_new = fit_and_substitute(temp_run_dict[reference_tag][key+".t"], t_new, ytable[:, ii])
                        ytable_new = np.vstack((ytable_new, y_new)) if ytable_new is not None else np.atleast_2d(y_new)
                    ref_dict[key][reference_tag] = ytable_new.T
                else:
                    if key+".x" in ref_dict:
                        # Copies existing time slice multiple times if only one time slice is present in the run
                        ytable_new = None
                        for ii in range(len(t_new)):
                            ytable_new = np.vstack((ytable_new, ytable)) if ytable_new is not None else np.atleast_2d(ytable)
                    ref_dict[key][reference_tag] = copy.deepcopy(ytable_new)
    # Loop over all runs in order to maintain run[0] for analysis purposes
    for tag, run_dict in temp_run_dict.items():
        # tag contains the id of the run, key the variable to be plotted
        if tag == reference_tag:
            for key in ref_dict:
                if not key.endswith(".x") and not key.endswith(".t"):
                    if key not in out_dict:
                        out_dict[key] = {}
                    out_dict[key][tag] = ref_dict[key][tag]
                else:
                    out_dict[key] = ref_dict[key]
        else:
            for key in run_dict:
                if not key.endswith(".x") and not key.endswith(".t"):
                    if key not in out_dict:
                        out_dict[key] = {}
                    ytable = np.atleast_2d(run_dict[key])
                    ytable_temp = None
                    # Perform radial vector interpolation, if radial vector is present in signal
                    if key+".x" in ref_dict:
                        x_new = ref_dict[key+".x"]
                        for ii in range(ytable.shape[0]):
                            y_new = fit_and_substitute(run_dict[key+".x"], x_new, ytable[ii, :])
                            ytable_temp = np.vstack((ytable_temp, y_new)) if ytable_temp is not None else np.atleast_2d(y_new)
                    else:
                        ytable_temp = np.atleast_2d(ytable)
                    # Perform time vector interpolation, always present
                    t_new = ref_dict[key+".t"]
                    ytable_new = None
                    if len(run_dict[key+".t"]) > 1:
                        if key+".x" in ref_dict:
                            for ii in range(ytable_temp.shape[1]):
                                y_new = fit_and_substitute(run_dict[key+".t"], t_new, ytable_temp[:, ii])
                                ytable_new = np.vstack((ytable_new, y_new)) if ytable_new is not None else np.atleast_2d(y_new)
                        else:
                            ytable_new = fit_and_substitute(run_dict[key+".t"], t_new, ytable_temp[0])

                        if ytable_new is not None:
                            ytable_new = ytable_new.T
                    else:
                        if key+".x" in run_dict:
                            # Copies existing time slice multiple times if only one time slice is present in the run
                            for ii in range(len(t_new)):
                                ytable_new = np.vstack((ytable_new, ytable_temp)) if ytable_new is not None else np.atleast_2d(ytable_temp)
                    out_dict[key][tag] = copy.deepcopy(ytable_new)
    return out_dict

def plot_traces(plot_data, plot_vars=None, single_time_reference=False):
    signal_list = plot_data["time_signals"] if "time_signals" in plot_data else keys_list['time_trace']
    if isinstance(plot_vars, list):
        signal_list = plot_vars
    for signame in signal_list:
        pdata = {}
        t_basis = None
        first_run = None
        for run in plot_data:
            if signame in plot_data[run]:
                pdata[run] = {"time": plot_data[run][signame+".t"], "data": plot_data[run][signame]}
                if first_run is not None and t_basis is None:
                    t_basis = pdata[run]["time"]
                if first_run is None:
                    first_run = run
                    if not single_time_reference:
                        t_basis = pdata[run]["time"]
        if pdata:
            print("Plotting %s" % (signame))
            fig = plt.figure()
            ax = fig.add_subplot(111)
            for run in pdata:
                xdata = pdata[run]["time"]
                ydata = pdata[run]["data"]
                linestyle = '-'
                linecolor = None
                if run == first_run and single_time_reference:
                    xdata = np.array([np.nanmin(t_basis), np.nanmax(t_basis)])
                    ydata = np.full(xdata.shape, pdata[run]["data"][0])
                    linestyle = '--'
                    linecolor = 'k'
                ax.plot(xdata, ydata, label=run, c=linecolor, ls=linestyle)
            ax.set_xlabel("time (s)")
            ax.set_ylabel(signame)
            ax.legend(loc='best')
#            fig.savefig(signame+".png", bbox_inches="tight")
            plt.show()

def plot_interpolated_traces(interpolated_data, plot_vars=None):
    signal_list = interpolated_data["time_signals"] if "time_signals" in interpolated_data else keys_list['time_trace']
    if isinstance(plot_vars, list):
        signal_list = plot_vars
    for signame in signal_list:
        if signame in interpolated_data:
            print("Plotting %s" % (signame))
            fig = plt.figure()
            ax = fig.add_subplot(111)

            for run in interpolated_data[signame]:
                ax.plot(interpolated_data[signame+".t"], interpolated_data[signame][run].flatten(), label=run)
            ax.set_xlabel("time (s)")
            ax.set_ylabel(signame)
            ax.legend(loc='best')
#            fig.savefig(signame+".png", bbox_inches="tight")
            plt.show()

def plot_gif_profiles(plot_data, plot_vars=None, single_time_reference=False):
    signal_list = plot_data["profile_signals"] if "profile_signals" in plot_data else keys_list['profiles_1d']
    if isinstance(plot_vars, list):
        signal_list = plot_vars
    for signame in signal_list:
        pdata = {}
        first_run = None
        tvec = None
        for run in plot_data:
            if signame in plot_data[run]:
                pdata[run] = []
                if first_run is None:
                    first_run = run
                    if not single_time_reference:
                        for tidx in range(len(plot_data[run][signame])):
                            pdata[run].append({"time": plot_data[run][signame+".t"][tidx], "rho": plot_data[run][signame][tidx]["x"], "data": plot_data[run][signame][tidx]["y"]})
                            tvec = np.hstack((tvec, plot_data[run][signame+".t"][tidx])) if tvec is not None else np.array([plot_data[run][signame+".t"][tidx]])
                else:
                    tvec_new = np.array([])
                    tvec_final = np.array([])
                    tidxvec = []
                    for tidx in range(len(plot_data[run][signame])):
                        tvec_new = np.hstack((tvec_new, plot_data[run][signame+".t"][tidx]))
                    if tvec is None:
                        tvec = tvec_new.copy()
                    for tidx_orig in range(len(tvec)):
                        tidx = np.abs(tvec[tidx_orig] - tvec_new).argmin(0)
                        pdata[run].append({"time": plot_data[run][signame+".t"][tidx], "rho": plot_data[run][signame][tidx]["x"], "data": plot_data[run][signame][tidx]["y"]})
                        tvec_final = np.hstack((tvec_final, plot_data[run][signame+".t"][tidx]))
        if pdata and single_time_reference:
            if tvec is None:
                for tidx in range(len(plot_data[first_run][signame])):
                    tvec = np.hstack((tvec, plot_data[first_run][signame+".t"][tidx])) if tvec is not None else np.array([plot_data[first_run][signame+".t"][tidx]])
            for tidx in range(len(tvec)):
                pdata[first_run].append({"time": tvec[tidx], "rho": plot_data[first_run][signame][0]["x"], "data": plot_data[first_run][signame][0]["y"]})

        if pdata:
            print("Plotting %s" % (signame))
            Figure = plt.figure()

            # creating a plot
            # lines_plotted = plt.plot([])

            ax = Figure.add_subplot(1, 1, 1)
            ax.set_xlabel('rho_tor_norm')
            ax.set_ylabel(signame)
            #ax.set_xlabel(r'$\rho$ [-]')
            #ax.set_ylabel(ylabel + ' ' + units)
            ymin = None
            ymax = None
            plot_list = {}
            for run in pdata:
                linestyle = '-'
                linecolor = None
                if run == first_run and single_time_reference:
                    linestyle = '--'
                    linecolor = 'k'
                pp = ax.plot(pdata[run][0]["rho"], pdata[run][0]["data"], label=run, c=linecolor, ls=linestyle)
                for tidx in range(len(pdata[run])):
                    ymin = np.nanmin([ymin, np.nanmin(pdata[run][tidx]["data"])]) if ymin is not None else np.nanmin(pdata[run][tidx]["data"])
                    ymax = np.nanmax([ymax, np.nanmax(pdata[run][tidx]["data"])]) if ymax is not None else np.nanmax(pdata[run][tidx]["data"])
                plot_list[run] = pp[0]

            ax.legend(loc='best')

            # putting limits on x axis since it is a trigonometry function (0,2)

            ax.set_xlim([0,1])

            # putting limits on y since it is a cosine function
            ax.set_ylim([ymin,ymax])

            # function takes frame as an input
            def AnimationFunction(frame):

                # line is set with new values of x and y
                for run in pdata:
                    plot_list[run].set_data((pdata[run][frame]["rho"], pdata[run][frame]["data"]))

            # creating the animation and saving it with a name that does not include spaces

            anim_created = FuncAnimation(Figure, AnimationFunction, frames=len(tvec), interval=200)
            #ylabel = ylabel.replace(' ', '_')
            #f = r'/afs/eufus.eu/user/g/g2mmarin/imas_scripts/animation' + ylabel + '.gif'
            #anim_created.save(f, writer='writergif')

            # displaying the video

            video = anim_created.to_html5_video()
            html = display.HTML(video)
            display.display(html)

            plt.show()

            # good practice to close the plt object.
            plt.close()

def plot_gif_interpolated_profiles(interpolated_data, plot_vars=None):
    signal_list = interpolated_data["profile_signals"] if "profile_signals" in interpolated_data else keys_list['profiles_1d']
    if isinstance(plot_vars, list):
        signal_list = plot_vars
    for signame in signal_list:
        first_run = None
        tvec = None
        if signame in interpolated_data:

            print("Plotting %s" % (signame))
            Figure = plt.figure()

            # creating a plot
            #    lines_plotted = plt.plot([])

            ax = Figure.add_subplot(1, 1, 1)
            ax.set_xlabel('rho_tor_norm')
            ax.set_ylabel(signame)
            #ax.set_xlabel(r'$\rho$ [-]')
            #ax.set_ylabel(ylabel + ' ' + units)
            ymin = None
            ymax = None
            plot_list = {}

            for run in interpolated_data[signame]:
                pp = ax.plot(interpolated_data[signame+".x"], interpolated_data[signame][run][0], label=run)
                for tidx in range(len(interpolated_data[signame+".t"])):
                    ymin = np.nanmin([ymin, np.nanmin(interpolated_data[signame][run][tidx])]) if ymin is not None else np.nanmin(interpolated_data[signame][run][tidx])
                    ymax = np.nanmax([ymax, np.nanmax(interpolated_data[signame][run][tidx])]) if ymax is not None else np.nanmax(interpolated_data[signame][run][tidx])
                plot_list[run] = pp[0]

            ax.legend(loc='best')

            # putting limits on x axis since it is a trigonometry function (0,2)

            ax.set_xlim([0,1])

            # putting limits on y since it is a cosine function
            ax.set_ylim([ymin,ymax])

            # function takes frame as an input
            def AnimationFunction(frame):

                # line is set with new values of x and y
                for run in interpolated_data[signame]:
                    plot_list[run].set_data((interpolated_data[signame+".x"], interpolated_data[signame][run][frame]))

            # creating the animation and saving it with a name that does not include spaces

            anim_created = FuncAnimation(Figure, AnimationFunction, frames=len(interpolated_data[signame+".t"]), interval=200)
            #ylabel = ylabel.replace(' ', '_')
            #f = r'/afs/eufus.eu/user/g/g2mmarin/imas_scripts/animation' + ylabel + '.gif'
            #anim_created.save(f, writer='writergif')

            # displaying the video

            video = anim_created.to_html5_video()
            html = display.HTML(video)
            display.display(html)

            plt.show()

            # good practice to close the plt object.
            plt.close()

def print_time_traces(data_dict, data_vars=None, inverted_layout=False):
    out_dict = {}
    signal_list = data_dict["time_signals"] if "time_signals" in data_dict else keys_list['time_trace']
    if isinstance(data_vars, list):
        signal_list = data_vars
    for signame in signal_list:
        if inverted_layout:
            if signame in data_dict:
                for run in data_dict[signame]:
                    if len(data_dict[signame][run]) > 0:
                        if run not in out_dict:
                            out_dict[run] = {}
                        val = np.mean(data_dict[signame][run])
                        print("%s %s average: %10.6e" % (run, signame, float(val)))
                        out_dict[run][signame] = val
        else:
            for run in data_dict[signame]:
                if signame in data_dict and len(data_dict[run][signame]) > 0:
                    if run not in out_dict:
                        out_dict[run] = {}
                    val = np.mean(data_dict[run][signame])
                    print("%s %s average: %10.6e" % (run, signame, float(val)))
                    out_dict[run][signame] = val
    return out_dict

def print_time_trace_errors(time_error_dict, custom_vars=None):
    out_dict = {}
    signal_list = time_error_dict["time_signals"] if "time_signals" in time_error_dict else expand_error_keys('time_trace')
    if isinstance(custom_vars, list):
        signal_list = custom_vars
    for signame in signal_list:
        if signame in time_error_dict:
            for run in time_error_dict[signame]:
                if signame not in out_dict:
                    out_dict[signame] = {}
                val = np.mean(time_error_dict[signame][run][np.where(np.isnan(time_error_dict[signame][run]), False, True)])
                print("%s %s average error: %10.6e" % (run, signame, float(val)))
                out_dict[signame][run] = val
    return out_dict

def print_profile_errors(profile_error_dict, custom_vars=None):
    out_dict = {}
    signal_list = profile_error_dict["time_signals"] if "time_signals" in profile_error_dict else expand_error_keys('time_trace')
    if isinstance(custom_vars, list):
        signal_list = custom_vars
    for signame in signal_list:
        if signame in profile_error_dict:
            for run in profile_error_dict[signame]:
                if signame not in out_dict:
                    out_dict[signame] = {}
                val = np.mean(profile_error_dict[signame][run][np.where(np.isnan(profile_error_dict[signame][run]), False, True)])
                print("%s %s average error: %10.6e" % (run, signame, float(val)))
                out_dict[signame][run] = val
    return out_dict

def absolute_error(data1, data2):
    return np.abs(data1 - data2)

def compute_absolute_error_for_all_traces(analysis_dict):
    out_dict = {}
    out_signal_list = []
    signal_list = analysis_dict["time_signals"] if "time_signals" in analysis_dict else keys_list['time_trace']
    for signame in signal_list:
        if signame in analysis_dict and len(analysis_dict[signame]) > 1:
            first_run = None
            first_data = None
            for run in analysis_dict[signame]:
                if first_data is None:
                    first_run = run
                    first_data = analysis_dict[signame][first_run]
                else:
                    var = signame+".absolute_error"
                    if var not in out_dict:
                        out_dict[var] = {}
                    comp_data = absolute_error(analysis_dict[signame][run].flatten(), first_data.flatten())
                    out_dict[var][run+":"+first_run] = comp_data.copy()
                    out_dict[var+".t"] = analysis_dict[signame+".t"]
                    out_signal_list.append(var)
    out_dict["time_signals"] = out_signal_list
    return out_dict

def compute_average_absolute_error_for_all_profiles(analysis_dict):
    out_dict = {}
    out_signal_list = []
    signal_list = analysis_dict["profile_signals"] if "profile_signals" in analysis_dict else keys_list['profiles_1d']
    for signame in signal_list:
        if signame in analysis_dict and len(analysis_dict[signame]) > 1:
            first_run = None
            first_data = None
            for run in analysis_dict[signame]:
                if first_data is None:
                    first_run = run
                    first_data = analysis_dict[signame][first_run]
                else:
                    var = signame+".average_absolute_error"
                    if var not in out_dict:
                        out_dict[var] = {}
                    comp_data = absolute_error(analysis_dict[signame][run], first_data)
                    out_dict[var][run+":"+first_run] = np.average(comp_data, axis=1)
                    out_dict[var+".t"] = analysis_dict[signame+".t"]
                    out_signal_list.append(var)
    out_dict["profile_signals"] = out_signal_list
    return out_dict

def perform_time_trace_analysis(analysis_dict, **kwargs):
    out_dict = {}
    out_signal_list = []
    absolute_error_flag = kwargs.pop("absolute_error", False)
    if absolute_error_flag:
        abs_err_dict = compute_absolute_error_for_all_traces(analysis_dict)
        signal_list = abs_err_dict.pop("time_signals")
        out_dict.update(abs_err_dict)
        out_signal_list.extend(signal_list)
    out_dict["time_signals"] = out_signal_list
    return out_dict

def perform_profile_analysis(analysis_dict, **kwargs):
    out_dict = {}
    out_signal_list = []
    average_absolute_error_flag = kwargs.pop("average_absolute_error", False)
    if average_absolute_error_flag:
        avg_abs_err_dict = compute_average_absolute_error_for_all_profiles(analysis_dict)
        signal_list = avg_abs_err_dict.pop("profile_signals")
        out_dict.update(avg_abs_err_dict)
        out_signal_list.extend(signal_list)
    out_dict["time_signals"] = out_signal_list
    return out_dict

def perform_sign_correction(raw_dict, ref_tag):
    # Only handles the index levels in order from get_onedict()
    for tag in raw_dict:
        if tag != ref_tag:
            for key in raw_dict[tag]:
                if not key.endswith(".x") and not key.endswith(".t") and key in raw_dict[ref_tag]:
                    if isinstance(raw_dict[tag][key][0], dict):
                        for ii in range(len(raw_dict[tag][key])):
                            if np.mean(raw_dict[ref_tag][key][ii]["y"]) * np.mean(raw_dict[tag][key][ii]["y"]) < 0.0:
                                raw_dict[tag][key][ii]["y"] = -raw_dict[tag][key][ii]["y"]
                    elif np.mean(raw_dict[ref_tag][key]) * np.mean(raw_dict[tag][key]) < 0.0:
                        raw_dict[tag][key] = -raw_dict[tag][key]
    return raw_dict

def standardize_basis_vectors(raw_dict, ref_tag, time_basis=None):

    # Transform reference data into the required field names and store in reference container
    ref_dict = {}
    for key in raw_dict[ref_tag]:
        if not key.endswith(".x") and not key.endswith(".t"):

            if key not in ref_dict:
                ref_dict[key] = {}

            if time_basis is None:

                ref_dict[key][ref_tag] = copy.deepcopy(raw_dict[ref_tag][key])
                if key+".x" in raw_dict[ref_tag]:
                    ref_dict[key+".x"] = copy.deepcopy(raw_dict[ref_tag][key+".x"])
                ref_dict[key+".t"] = copy.deepcopy(raw_dict[ref_tag][key+".t"])

            else:    # Apply user-defined time vector as interpolation basis

                # User-defined time vector takes priority over the time vector inside the user-defined reference run
                ytable = np.atleast_2d(raw_dict[ref_tag][key])

                # Radial interpolation will take place in the next loop
                if key+".x" in raw_dict[ref_tag]:
                    ref_dict[key+".x"] = copy.deepcopy(raw_dict[ref_tag][key+".x"])
                ref_dict[key+".t"] = copy.deepcopy(time_basis)

                # Perform time vector interpolation, always present
                t_new = ref_dict[key+".t"]
                if len(raw_dict[ref_tag][key+".t"]) > 1:
                    ytable_new = None
                    for ii in range(ytable.shape[1]):
                        y_new = fit_and_substitute(raw_dict[ref_tag][key+".t"], t_new, ytable[:, ii])
                        ytable_new = np.vstack((ytable_new, y_new)) if ytable_new is not None else np.atleast_2d(y_new)
                    ref_dict[key][ref_tag] = ytable_new.T
                else:
                    # Copies existing time slice multiple times if only one time slice is present in the run
                    ytable_new = None
                    for ii in range(len(t_new)):
                        ytable_new = np.vstack((ytable_new, ytable)) if ytable_new is not None else np.atleast_2d(ytable)
                    ref_dict[key][reference_tag] = copy.deepcopy(ytable_new)

    # Loop over all runs in order to maintain run[0] for analysis purposes
    std_dict = {}
    for tag, run_dict in raw_dict.items():
        # tag contains the id of the run, key the variable to be plotted
        if tag == ref_tag:
            for key in ref_dict:
                if not key.endswith(".x") and not key.endswith(".t"):
                    if key not in std_dict:
                        std_dict[key] = {}
                    std_dict[key][tag] = ref_dict[key][tag]
                else:
                    std_dict[key] = ref_dict[key]
        elif tag not in ["time_signals", "profile_signals"]:
            for key in run_dict:
                if not key.endswith(".x") and not key.endswith(".t"):

                    if key not in std_dict:
                        std_dict[key] = {}

                    ytable = np.atleast_2d(run_dict[key])
                    ytable_temp = None
                    # Perform radial vector interpolation, if radial vector is present in signal
                    if key+".x" in ref_dict:
                        x_new = ref_dict[key+".x"]
                        for ii in range(ytable.shape[0]):
                            y_new = fit_and_substitute(run_dict[key+".x"], x_new, ytable[ii, :])
                            ytable_temp = np.vstack((ytable_temp, y_new)) if ytable_temp is not None else np.atleast_2d(y_new)
                    else:
                        ytable_temp = np.atleast_2d(ytable)

                    ytable_new = None
                    # Perform time vector interpolation, always present
                    t_new = ref_dict[key+".t"]
                    if len(run_dict[key+".t"]) > 1:
                        if key+".x" in run_dict:
                            for ii in range(ytable_temp.shape[1]):
                                y_new = fit_and_substitute(run_dict[key+".t"], t_new, ytable_temp[:, ii])
                                ytable_new = np.vstack((ytable_new, y_new)) if ytable_new is not None else np.atleast_2d(y_new)
                        else:
                            ytable_new = fit_and_substitute(run_dict[key+".t"], t_new, ytable_temp[0])
                        if ytable_new is not None:
                            ytable_new = ytable_new.T
                    else:
                        # Copies existing time slice multiple times if only one time slice is present in the run
                        for ii in range(len(t_new)):
                            ytable_new = np.vstack((ytable_new, ytable_temp)) if ytable_new is not None else np.atleast_2d(ytable_temp)

                    std_dict[key][tag] = copy.deepcopy(ytable_new)
        else:
            std_dict[tag] = run_dict

    return std_dict

def compute_user_string_functions(data_dict, signal_operations, standardized=False):

    # Oof, this is not the safest implementation (due to eval) but it takes a lot to make this both general and clean
    if not standarized:          # This is for the raw vector branch
        for tag in taglist:
            for op, sigopvec in signal_operations.items():

                # Standardizing basis vectors across operated signals, which may be different between different IDSs
                operation_dict = {}
                time_ref = None
                radial_ref = None
                for key in sigopvec:
                    if time_ref is None and key+".t" in data_dict[tag]:
                        time_ref = data_dict[tag][key+".t"]
                    if radial_ref is None and key+".x" in data_dict[tag]:
                        radial_ref = data_dict[tag][key+".x"]

                    ytable = np.atleast_2d(data_dict[tag][key])
                    ytable_temp = None
                    if radial_ref is not None and key+".x" in data_dict[tag]:
                        for ii in range(ytable.shape[0]):
                            y_new = fit_and_substitute(data_dict[tag][key+".x"], radial_ref, ytable[ii, :])
                            ytable_temp = np.vstack((ytable_temp, y_new)) if ytable_temp is not None else np.atleast_2d(y_new)
                    else:
                        ytable_temp = np.atleast_2d(ytable)

                    ytable_new = None
                    if time_ref is not None and len(data_dict[key+".t"]) > 1:
                        if key+".x" in data_dict:
                            for ii in range(ytable_temp.shape[1]):
                                y_new = fit_and_substitute(data_dict[tag][key+".t"], time_ref, ytable_temp[:, ii])
                                ytable_new = np.vstack((ytable_new, y_new)) if ytable_new is not None else np.atleast_2d(y_new)
                        else:
                            ytable_new = fit_and_substitute(data_dict[tag][key+".t"], time_ref, ytable_temp[0])
                    else:
                        ytable_new = copy.deepcopy(ytable_temp)
                    if ytable_new is not None:
                        ytable_new = ytable_new.T

                    operation_dict[key] = copy.deepcopy(ytable_new)

                # Substituting the key since otherwise it will think that the dots define attributes
                sfunc = op.replace('.', '_')
                nkey_list = []
                fready = True
                for key in sigopvec:
                    new_key = key.replace('.', '_')
                    nkey_list.append(new_key)
                    if key not in operation_dict:
                        fready = False

                if fready:
                    for new_key in nkey_list:
                        globals()[new_key] = copy.deepcopy(operation_dict[key])
                    op_result = eval(sfunc)
                    data_dict[tag][op] = op_result
                    data_dict[tag][op+'.t'] = time_ref
                    if radial_ref is not None:
                        data_dict[tag][op+'.x'] = radial_ref
                        data_dict["profile_signals"].append(op)
                    else:
                        data_dict["time_signals"].append(op)
                    for new_key in nkey_list:
                        del globals()[new_key]

    else:                            # This is for the standardized vector branch
        for op, sigopvec in signal_operations.items():

            # Substituting the key since otherwise it will think that the dots define attributes
            sfunc = op.replace('.', '_')
            nkey_list = []
            fready = True
            fradial = False
            for key in sigopvec:
                new_key = key.replace('.', '_')
                nkey_list.append(new_key)
                if new_key not in out_dict:
                    fready = False
                if key+".x" in out_dict:
                    fradial = True

            if fready:
                operation_dict = {}
                for tag in taglist:
                    for new_key in nkey_list:
                        globals()[new_key] = copy.deepcopy(data_dict[key][tag])
                    op_result = eval(sfunc)
                    operation_dict[tag] = op_result
                    for new_key in nkey_list:
                        del globals()[new_key]
                data_dict[op] = copy.deepcopy(operation_dict)
                if fradial:
                    data_dict["profile_signals"].append(op)
                else:
                    data_dict["time_signals"].append(op)

    return data_dict

def generate_metadata_table(dblist, shotlist, runlist, userlist, sourcelist=None, transportlist=None):

    mlist = dblist if isinstance(dblist, (list, tuple)) else []
    plist = shotlist if isinstance(shotlist, (list, tuple)) else []
    rlist = runlist if isinstance(runlist, (list, tuple)) else []
    ulist = userlist if isinstance(userlist, (list, tuple)) else []
    slist = sourcelist if isinstance(sourcelist, (list, tuple)) else []
    tlist = transportlist if isinstance(transportlist, (list, tuple)) else []

    n_m = len(mlist)
    n_p = len(plist)
    n_r = len(rlist)
    n_u = len(ulist)
    n_s = len(slist)
    n_t = len(tlist)
    nmax = max(n_m, n_p, n_r, n_u, n_s, n_t)
    print(n_m, n_p, n_r, n_u, n_s, n_t, nmax)

    mlist = extend_list(mlist, nmax)
    plist = extend_list(plist, nmax)
    rlist = extend_list(rlist, nmax)
    ulist = extend_list(ulist, nmax)
    slist = extend_list(slist, nmax)
    tlist = extend_list(tlist, nmax)

    outlist = []
    for spec in zip(mlist, plist, rlist, ulist, slist, tlist):
        outlist.append(spec)

    return outlist

def generate_data_tables(run_specs, signals, time_begin, time_end, signal_operations=None, correct_sign=False, reference_index=None, standardize=False, time_basis=None):

    ref_idx = reference_index if isinstance(reference_index, int) else 0

    # Adding the variables for comparison of functions when they are not available
    sigvec = copy.deepcopy(signals)
    sigopdict = {}
    fops = False
    if isinstance(signal_operations, list):
        for sigop in signal_operations:
            sigop_tmp = copy.deepcopy(sigop)
            for op in operations:
                sigop_tmp = sigop_tmp.replace(op, ';')
            sigop_vars = sigop_tmp.split(';')
            fops = True
            empty_vars = []
            for ii in len(sigop_vars):
                if sigop_vars[ii] == '':
                    empty_vars.append(ii)
            for ii in empty_vars[::-1]:
                del sigop_vars[ii]
            for var in sigop_vars:
                if var not in sigvec:
                    sigvec.append(var)
            sigopdict[sigop] = sigop_vars

    raw_dict = {}
    ref_tag = None

    taglist = []
    t_fields = []
    xt_fields = []
    for ii, spec in enumerate(run_specs):

        db = spec[0]
        shot = spec[1]
        runid = spec[2]
        user = spec[3]
        sid = spec[4]
        tid = spec[5]
        tag = "%s/%s/%d/%d" % (user, db, shot, runid)

        #print(tag, sid, tid)

        onedict = get_onedict(sigvec, user, db, shot, runid, time_begin, time_end=time_end, sid=sid, tid=tid, interpolate=standardize)
        if ii == ref_idx:
            ref_tag = tag
        if "time_signals" in onedict:
            for signame in onedict["time_signals"]:
                if signame not in t_fields:
                    t_fields.append(signame)
            del onedict["time_signals"]
        if "profile_signals" in onedict:
            for signame in onedict["profile_signals"]:
                if signame not in xt_fields:
                    xt_fields.append(signame)
            del onedict["profile_signals"]
        raw_dict[tag] = onedict
        taglist.append(tag)

    raw_dict["time_signals"] = t_fields
    raw_dict["profile_signals"] = xt_fields

    out_dict = {}
    if raw_dict and ref_tag is not None:

        out_dict = copy.deepcopy(raw_dict)

        # Changes the sign of the variable if it is mismatching with reference run. Useful for q profile in some instances.
        # NOTE: this implementation requires the index level order from get_onedict()
        if correct_sign:
            out_dict = perform_sign_correction(out_dict, ref_tag)

        # Standardizes the radial and time vectors to the reference run
        # NOTE: this implementation inverts the run tag and signal index levels within the nested dict!!!
        if standardize:
            out_dict = standardize_basis_vectors(out_dict, ref_tag, time_basis=time_basis)

        # Applies user-defined string operations to single and/or multiple variables
        # NOTE: this implementation uses eval to process string operations!!! BE CAREFUL!!!
        if fops:
            out_dict = compute_user_string_functions(out_dict, sigopdict, standardized=standardize)

    return out_dict, ref_tag

####### SCRIPT #######

def compare_runs(signals, dblist, shotlist, runlist, time_begin, time_end=None, time_basis=None, userlist=None, sourcelist=None, transportlist=None, plot=False, analyze=False, correct_sign=False, steady_state=False, uniform=False, signal_operations=None):

    ref_idx = 1 if steady_state else 0
    standardize = (uniform or analyze or isinstance(time_basis, (list, tuple, np.ndarray)))

    runvec = generate_metadata_table(dblist, shotlist, runlist, userlist, sourcelist, transportlist)

    data_dict, ref_tag = generate_data_tables(runvec, signals, time_begin, time_end=time_end, signal_operations=signal_operations, correct_sign=correct_sign, reference_index=ref_idx, standardize=standardize, time_basis=time_basis)

#    # Only variables in the keys_list will be plotted
#    if multi_var_function:
#        keys_list['time_trace'].append(multi_var_function)

#    if not uniform and plot:
#        plot_traces(plot_dict, single_time_reference=steady_state)
#        plot_gif_profiles(plot_dict, single_time_reference=steady_state)

#    analysis_dict = standardize_manydict(runvec, sigvec, time_begin, time_end=time_end, time_vector=time_basis, set_reference=ref_tag)

    # Changing the sign of the variable also in the analysis_dict when needed (should not be needed in the future)
#    if correct_sign:
#        for key in analysis_dict:
#            if not key.endswith(".x") and not key.endswith(".t"):
#                first_index = 0
#                for tag in analysis_dict[key]:
#                    if first_index:
#                        analysis_dict[key][tag] = -analysis_dict[key][tag]
#                    first_index += 1


    # ------------- Adding comparison of functions ------------
    # Adding the possibility of comparing functions of variables.
    # Need to interpolate in space and time when the signals are coming from different IDSs...
    # Only traces are supported for now, so no space interpolation

#    if sigops:
#        # Changing time vector if it is different between different IDSs
#        for key in variables_multi_var_function:
#            time_ref = None
#            for tag in analysis_dict[key]:
#                if time_ref is None:
#                    time_ref = analysis_dict[key+'.t']

#                analysis_dict[key][tag] = fit_and_substitute(analysis_dict[key+".t"], time_ref, analysis_dict[key][tag])

        # Building an array in place of the dictionary to simplify the operation later
#        analysis_array = {}
#        for key in variables_multi_var_function:
#            analysis_array[key] = None
#            for tag in analysis_dict[key]:
#                if analysis_array[key] is not None:
#                    analysis_array[key] = np.hstack((analysis_array[key], analysis_dict[key][tag]))
#                else:
#                    analysis_array[key] = analysis_dict[key][tag]
        # Substituting the key since otherwise it will think that the dots define attributes
#        multi_var_function = multi_var_function.replace('.', '_')
#        for key in variables_multi_var_function:
#            new_key = key.replace('.', '_')
#            globals()[new_key] = analysis_array[key]

#        new_variable = eval(multi_var_function)
#        new_variable = new_variable.reshape(len(analysis_dict[key]),len(time_ref))

#        for key in variables_multi_var_function:
#            new_key = key.replace('.', '_')
#            del globals()[new_key]

#        analysis_dict[multi_var_function] = {}
#        for new_slice, tag in zip(new_variable, analysis_dict[variables_multi_var_function[0]]):
            
#            analysis_dict[multi_var_function][tag] = new_slice
#            analysis_dict[multi_var_function+'.t'] = time_ref

        # Already done above
        #keys_list['time_trace'].append(multi_var_function)

    # -------------------------------------------------------------------------

    if plot:
        if standardize:
            plot_interpolated_traces(data_dict)
            plot_gif_interpolated_profiles(data_dict)
        else:
            plot_traces(data_dict, single_time_reference=steady_state)
            plot_gif_profiles(data_dict, single_time_reference=steady_state)

    time_averages = print_time_traces(data_dict, inverted_layout=standardize)

    if analyze:

        options = {"absolute_error": True}
        time_error_dict = perform_time_trace_analysis(data_dict, **options)

        if plot:
            plot_interpolated_traces(time_error_dict)

        options = {"average_absolute_error": True}
        profile_error_dict = perform_profile_analysis(data_dict, **options)

        if plot:
            plot_interpolated_traces(profile_error_dict)

        time_error_averages = print_time_trace_errors(time_error_dict)
        profile_error_averages = print_profile_errors(profile_error_dict)


####### COMMAND LINE INTERFACE #######

def main():

    args = input()
    do_plot = not args.calc_only
    compare_runs(
        signals=args.signal,
        dblist=args.database,
        shotlist=args.shot,
        runlist=args.run,
        time_begin=args.time_begin,
        time_end=args.time_end,
        userlist=args.user,
        time_basis=args.time_out,
        sourcelist=args.source,
        transportlist=args.transport,
        plot=do_plot,
        analyze=args.analyze,
        correct_sign=args.correct_sign,
        steady_state=args.steady_state,
        uniform=args.uniform,
        signal_operations=args.function
    )
    # Arugments not used: save_plot, version

if __name__ == "__main__":
    main()
