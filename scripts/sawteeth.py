import scipy
import scipy.io
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d, UnivariateSpline
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import imas,os,datetime,sys
from imas import imasdef
import getpass
import math


def read_math_file(mat_file_name):

    mat = scipy.io.loadmat(mat_file_name)

    sawteeth_data = {}
    sawteeth_data['t_crash'] = np.ndarray.flatten(mat['mpx'][0][0][0])
    sawteeth_data['t_start_crash'] = np.ndarray.flatten(mat['mpx'][0][0][1])
    sawteeth_data['t_stop_crash'] = np.ndarray.flatten(mat['mpx'][0][0][2])
    sawteeth_data['tau_st'] = np.ndarray.flatten(mat['mpx'][0][0][3])
    sawteeth_data['f_st'] = np.ndarray.flatten(mat['mpx'][0][0][4])
    sawteeth_data['t_peak'] = np.ndarray.flatten(mat['mpx'][0][0][5])
    sawteeth_data['t_start_peak'] = np.ndarray.flatten(mat['mpx'][0][0][6])
    sawteeth_data['t_stop_peak'] = np.ndarray.flatten(mat['mpx'][0][0][7])
    sawteeth_data['chan_inv'] = mat['mpx'][0][0][8]
    sawteeth_data['rhopsi_inv'] = mat['mpx'][0][0][9]
    sawteeth_data['rhovol_inv'] = mat['mpx'][0][0][10]
    sawteeth_data['mean_prof_before_crash'] = mat['mpx'][0][0][11]
    sawteeth_data['mean_prof_after_crash'] = mat['mpx'][0][0][12]

    return sawteeth_data


def find_experimental_rho_equal_one(mat_file_name, time_start = None, time_end = None, verbose = False):
    
    sawteeth_data = read_math_file(mat_file_name)

    # Select the first crash after the first peak

    index_first_crash, time_first_crash = find_time_first_crash(sawteeth_data['t_crash'], sawteeth_data['t_peak'])

    rho_lfs = sawteeth_data['rhopsi_inv'][index_first_crash:,0]
    rho_hfs = sawteeth_data['rhopsi_inv'][index_first_crash:,1]
    time = sawteeth_data['t_crash'][index_first_crash:]

    if time_start:
        index_start = np.abs(time - time_start).argmin(0)
        time = time[index_start:]
        rho_lfs = rho_lfs[index_start:]
        rho_hfs = rho_hfs[index_start:]

    if time_end:
        index_end = np.abs(time - time_end).argmin(0)
        time = time[:index_end]
        rho_lfs = rho_lfs[:index_end]
        rho_hfs = rho_hfs[:index_end]

    # Put Nans to 0. They can be detrimental for the other steps of the code

    rho_lfs[np.isnan(rho_lfs)] = 0
    rho_hfs[np.isnan(rho_hfs)] = 0

    # Find the minimum difference between two consequent values in these arrays. This should be the 'line of sight error'

    min_difference = min(map(lambda x, y : abs(x - y), rho_lfs[1:], rho_lfs))
    if min_difference == 0:
        min_difference = sorted(set(map(lambda x, y : abs(x - y), rho_lfs[1:], rho_lfs)))[1]

    if verbose:

        print(rho_hfs)
        print(rho_lfs)
        print(min_difference)

        plt.subplot(1,1,1)
        plt.plot(time, rho_lfs, 'b-')
        plt.plot(time, rho_hfs, 'r-')
        plt.show()

    # Find the difference between the values of the two arrays (reflected on 0). This is an equilibrium error

    rho = (rho_hfs - rho_lfs)/2
    rho_error = np.sqrt(((rho_hfs-rho)**2 +(rho+rho_lfs)**2)/2)

    # Combine the two errors

    rho_error = np.sqrt(min_difference**2 +rho_error**2)

    if verbose:
        plt.subplot(1,1,1)
        plt.errorbar(time, rho, yerr=rho_error, fmt='b-')
        plt.show()

    return time, rho, rho_error

def find_modelled_rho_equal_value(db, shot, run, username = None, surface = 1, time_start = None, time_end = None):

    if not username:
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
    equilibrium = data_entry.get('equilibrium')

    data_entry.close()

    q_core_profiles, q_equilibrium = [], []
    time_cp = core_profiles.time

    # Cut arrays following the specification of a time start and a time end
    index_start, index_end = 0, len(time_cp)
    if time_start:
        index_start = np.abs(time_cp - time_start).argmin(0)
        time_cp = time_cp[index_start:]
    if time_end:
        index_end = np.abs(time_cp - time_end).argmin(0)
        time_cp = time_cp[:index_end]

    #x_cp = core_profiles.profiles_1d[0].grid.rho_tor_norm
    #x_cp = core_profiles.profiles_1d[0].grid.psi
    #x_cp = core_profiles.profiles_1d[0].grid.rho_pol_norm

    #for profile_1d in core_profiles.profiles_1d[index_start:index_end]:
    #    q_core_profiles.append(profile_1d.q)

    #q_core_profiles = np.asarray(q_core_profiles).reshape(len(time_cp), len(x_cp))

    # Also extracting the q profile from the equilibrium IDS

    time_eq = equilibrium.time

    # Again cutting the arrays when time start and time end are specified

    index_start, index_end = 0, len(time_eq)
    if time_start:
        index_start = np.abs(time_eq - time_start).argmin(0)
    if time_end:
        index_end = np.abs(time_eq - time_end).argmin(0)

    time_eq = time_eq[index_start:index_end]

    x_eq = equilibrium.time_slice[0].profiles_1d.rho_tor_norm

    # To be consistent with the math file, rho poloidal is calculated instead of rho toroidal
    psi_norm = []
    for time_slice_eq in equilibrium.time_slice[index_start:index_end]:
        psi = time_slice_eq.profiles_1d.psi
        psi_axis = time_slice_eq.global_quantities.psi_axis
        psi_boundary = time_slice_eq.global_quantities.psi_boundary

        #psi_norm.append(np.sqrt((psi-psi_axis)/(psi_boundary-psi_axis)))
        psi_norm.append((psi-psi_axis)/(psi_boundary-psi_axis))

    psi_norm = np.asarray(psi_norm)

    for time_slice_eq in equilibrium.time_slice[index_start:index_end]:
        q_equilibrium.append(time_slice_eq.profiles_1d.q)

    #q_equilibrium = np.asarray(q_equilibrium).reshape(len(time_eq), len(x_cp))
    q_equilibrium = np.asarray(q_equilibrium).reshape(len(time_eq), len(psi_norm[0]))

    # Fit to splines and find the 0

    #rho_q_equal_one = find_root_q_one(x_cp, q_core_profiles)
    rho_q_equal_one = find_root_q_one(psi_norm, q_equilibrium, surface = surface)

    rho_q_equal_one = np.asarray(rho_q_equal_one)
    rho_q_equal_one[rho_q_equal_one>0.7] = 0.7

    return time_cp, rho_q_equal_one


def find_root_q_one(x, q_profiles, surface = 1):

    rho_q_equal_one = []

    '''

    finds the y=surface point for the q profile. q=1 surface is the base, but can also work for different values. This because the inversion radius is not exactly at q=1. Can do for one rho or when rho is changing in time.

    '''

    if len(np.shape(x)) == 1:
        for q_profile in q_profiles:
            f_space_cp = interp1d(x, q_profile-surface, fill_value = 'extrapolate')
            root_found = scipy.optimize.root(f_space_cp, 1, tol = 1e-4)
            if root_found['success']:
                rho_q_equal_one.append(root_found['x'][0])
            else:
                rho_q_equal_one.append(0)

        rho_q_equal_one = [0 if x < 0.05 else x for x in rho_q_equal_one]

    elif len(np.shape(x)) == 2:
        for q_profile, x_value in zip(q_profiles, x):
            f_space_cp = interp1d(x_value, q_profile-surface, fill_value = 'extrapolate')
            root_found = scipy.optimize.root(f_space_cp, 1, tol = 1e-4)
            if root_found['success']:
                rho_q_equal_one.append(root_found['x'][0])
            else:
                rho_q_equal_one.append(0)

        rho_q_equal_one = [0 if x < 0.05 else x for x in rho_q_equal_one]

    return rho_q_equal_one

def plot_q_equal_one(db, shot, run, mat_file_name, username = None):

    time, rho, rho_error = find_experimental_rho_equal_one(mat_file_name)
    time_cp, rho_q_equal_one = find_modelled_rho_equal_value(db, shot, run)

    plt.subplot(1,1,1)
    plt.errorbar(time, rho, yerr=rho_error, fmt='b-')
    plt.plot(time_cp, rho_q_equal_one, 'g-')
    plt.show()

def plot_inversion_radius(db, shot, run, mat_file_name, time_start = None, time_end = None, username = None, verbose = None):

    if not time_start:
        time_start = 0
    if not time_end:
        time_end = 10000

    centre_q_1 = 1.1

    times, rhos, rho_errors_exp = find_experimental_rho_equal_one(mat_file_name, time_start = time_start, time_end = time_end)

    time_cp, rho_q_equal_one_up = np.asarray(find_modelled_rho_equal_value(db, shot, run, surface = centre_q_1-0.05, time_start = time_start, time_end = time_end))
    time_cp, rho_q_equal_one_down = np.asarray(find_modelled_rho_equal_value(db, shot, run, surface = centre_q_1+0.05, time_start = time_start, time_end = time_end))

    time_cp, rhos_model = find_modelled_rho_equal_value(db, shot, run, surface = centre_q_1, time_start = time_start, time_end = time_end)
    rho_errors_model = abs(rho_q_equal_one_up-rho_q_equal_one_down)/2

    # There should not be sawteeth earlier than 50ms. If it happens for some numerical reason, kill them. If I find a good reason for them to be triggered, delete the next two lines of code
    rhos_model = np.where(time_cp < 0.05, 0, rhos_model)
    rho_errors_model = np.where(time_cp < 0.05, 0, rho_errors_model)

    if verbose:
        plt.subplot(1,1,1)
        plt.errorbar(times, rhos, yerr=rho_errors_exp, fmt='b-', label = 'Inversion radius Exp')
        plt.errorbar(time_cp, rhos_model, yerr=rho_errors_model, fmt='g-', label = 'Inversion radius Model')
        plt.xlabel('time [s]')
        plt.ylabel(r'$ \rho $ [-]')
        plt.legend()

        plt.show()

    # Should still not go before or after the limits of the simulation, as it does not make sense to compare there...
    time_begin, time_end = min(time_cp), max(time_cp)
    index_start = np.abs(times - time_begin).argmin(0)+1
    index_end = np.abs(times - time_end).argmin(0)-1
    times, rhos, rho_errors_exp = times[index_start:index_end], rhos[index_start:index_end], rho_errors_exp[index_start:index_end]

    rhos_model_rebased = fit_and_substitute(time_cp, times, rhos_model)
    rho_errors_model_rebased = fit_and_substitute(time_cp, times, rho_errors_model)

    # Simple formula to calculate the agreement. Is there something better?
    agreement, time_plot = [], []

    for rho, rho_model, rho_error_exp, rho_error_model, time in zip(rhos, rhos_model_rebased, rho_errors_exp, rho_errors_model_rebased, times):
        if rho_error_exp != 0:
            agreement.append(math.sqrt(pow((rho - rho_model),2)/(pow(rho_error_exp,2) + pow(rho_error_model,2))))
            time_plot.append(time)

    time_plot, agreement = np.asarray(time_plot), np.asarray(agreement)
    mean_agreement = np.average(np.asarray(agreement))
    deviation_agreement = np.std(np.asarray(agreement))

    # Removing outliers, probably result of very small errorbars or diagnostic problems
    time_plot = time_plot[np.where(agreement == 0, False, True)]
    agreement = agreement[np.where(agreement == 0, False, True)]
    time_plot = time_plot[np.where(agreement > mean_agreement+5*deviation_agreement, False, True)]
    agreement = agreement[np.where(agreement > mean_agreement+5*deviation_agreement, False, True)]

    if verbose == 2:
        plt.subplot(1,1,1)
        plt.errorbar(time_plot, agreement, fmt='g-', label = 'Agreement')
        plt.xlabel('time [s]')
        plt.ylabel(r'Agreement [-]')
        plt.legend()

        plt.show()

    mean_agreement = np.average(np.asarray(agreement))

    print('The agreement for the sawteeth is: ' + str(mean_agreement))
    return(mean_agreement)

def plot_inversion_radius_sensitivity(db, shot, run, sensitivity_lenght, mat_file_name, username = None, time_start = 0, time_end = 1000):

# Should insert the option to set a time start and a time end

    '''

    Calculates and plots the inversion radius surface for experiment and model. Calculates the absolute and relative distance in rho


    '''

    centre_q_1 = 1.1

    time, rho, rho_error_exp = find_experimental_rho_equal_one(mat_file_name)

    index_start = np.abs(time - time_start).argmin(0)
    index_end = np.abs(time - time_end).argmin(0)
    time = time[index_start:index_end]
    rho = rho[index_start:index_end]
    rho_error_exp = rho_error_exp[index_start:index_end]

    rel_error_timedep = []

    style_list = create_line_list()
    labels = ['nominal', 'TE_09', 'TE_11', 'TI_09', 'TI_11', 'NE_09', 'NE_11', 'Z_09', 'Z_11', 'peak_09', 'peak_11', 'Q_09', 'Q_11']

    fig1 = plt.subplot(1,1,1)
    fig1.errorbar(time, rho, yerr=rho_error_exp, fmt='b-', label = 'Experimental')
    fig1.set_xlabel('time [s]')
    fig1.set_ylabel(r'$ \rho $ [-]')
    fig2, axs = plt.subplots(1,2)
    rel_error_array = []

    for sensitivity, style, label in zip(range(sensitivity_lenght), style_list, labels):
        time_cp, rho_q_equal_one = find_modelled_rho_equal_value(db, shot, run+sensitivity, surface = centre_q_1, time_start = 0, time_end = 1000)

# Remapping the time to be sure not to extrapolate the modelling data outside the region where data exist
# Need new variable to avoid continuosly chopping the experimental array (tomap)

        time_tomap = time[:]
        rho_tomap = rho[:]

# Can use it as a function maybe?

        if time_cp[0]>time[0]:
            index_start = np.abs(time - time_cp[0]).argmin(0)
            time_tomap = time_tomap[index_start:]
            rho_tomap = rho_tomap[index_start:]
        if time_cp[-1]<time[-1]:
            index_end = np.abs(time - time_cp[-1]).argmin(0)
            time_tomap = time_tomap[:index_end]
            rho_tomap = rho_tomap[:index_end]

        rho_q_equal_one = fit_and_substitute(time_cp, time_tomap, rho_q_equal_one)
        fig1.plot(time_tomap, rho_q_equal_one, style, label = label)

        denominator = np.abs(rho_q_equal_one+rho_tomap)
        denominator[denominator == 0.0] = 1.0
        rel_error_timedep.append(np.abs(rho_q_equal_one-rho_tomap)/denominator)
        rel_error_array.append(np.average(np.abs(rho_q_equal_one-rho_tomap)/denominator))
        axs[0].plot(time_tomap, rel_error_timedep[sensitivity], style, label = label)
        axs[0].set_xlabel('time [s]')
        axs[0].set_ylabel(r'$ \rho $ [-]')

    fig1.legend()

    axs[0].legend()

    axs[1].plot(range(len(rel_error_array)), rel_error_array, 'r-', label = r'$ \sigma_{abs} $ sensitivity')
    axs[1].set_xticks(range(len(rel_error_array)))
    axs[1].set_xticklabels(labels[:sensitivity_lenght])
    axs[1].set_ylabel(r'$ \rho $ [-]')
    axs[1].legend()

    plt.show()


def find_time_first_crash(t_crash_array, t_peak_array):

    index_first_crash = 0

    for ii, t_crash in enumerate(t_crash_array):
        if t_crash > t_peak_array[0]:
            index_first_crash = ii
            break

    return index_first_crash, t_crash_array[index_first_crash]

def create_line_list():

    color_list = 'b', 'g', 'r', 'c', 'm', 'y','k'
    line_list = '-', '--', '-.', ':', '.'

    style_list = []
    for line in line_list:
        for color in color_list:
            style_list.append(color+line)

    return style_list

def fit_and_substitute(x_old, x_new, data_old):

    f_space = interp1d(x_old, data_old, fill_value = 'extrapolate')

    variable = np.array(f_space(x_new))
    variable[variable > 1.0e25] = 0

    return variable


if __name__ == "__main__":

#    find_experimental_q0('sawteeth_64965.mat')
#    find_modelled_q0('tcv', 64862, 133)
#    plot_q_equal_one('tcv', 64862, 144, 'sawteeth_64965.mat')
    #plot_inversion_radius('tcv', 64965, 1800, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64965.mat', verbose = True)

    #plot_inversion_radius('tcv', 64954, 1816, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64954.mat', verbose = 2, time_start = 0.08)
    #plot_inversion_radius('tcv', 64954, 1804, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64954.mat', verbose = 2, time_start = 0.08)
    #plot_inversion_radius('tcv', 64954, 1800, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64954.mat', verbose = 2, time_start = 0.08)

    #plot_inversion_radius('tcv', 64954, 1803, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64954.mat', verbose = 2)
    #plot_inversion_radius('tcv', 64954, 1816, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64954.mat', verbose = 2)
    #plot_inversion_radius('tcv', 64954, 1804, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64954.mat', verbose = 2)
    plot_inversion_radius('tcv', 64954, 1800, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64954.mat', verbose = 2)


    #plot_inversion_radius('tcv', 64958, 1800, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64958.mat', verbose = True)
    plot_inversion_radius('tcv', 64862, 1800, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64862.mat', verbose = 2)
    #plot_inversion_radius('tcv', 56653, 1800, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_56653.mat', verbose = True)

##    plot_inversion_radius('tcv', 64958, 200, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64958.mat')
#    plot_inversion_radius_sensitivity('tcv', 64965, 200, 12, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64965.mat')
#    plot_inversion_radius_sensitivity('tcv', 64965, 200, 12, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64965.mat')
#    plot_inversion_radius_sensitivity('tcv', 64958, 200, 12, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64958.mat')
#    plot_inversion_radius_sensitivity('tcv', 64958, 220, 12, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64958.mat')

#    plot_inversion_radius('tcv', 56653, 123, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_56653.mat')
#    plot_inversion_radius_sensitivity('tcv', 56653, 120, 12, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_56653.mat', time_start = 0.05)
#    plot_inversion_radius_sensitivity('tcv', 64954, 220, 12, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64954.mat', time_start = 0.05)
#    plot_inversion_radius_sensitivity('tcv', 64862, 230, 12, '/afs/eufus.eu/user/g/g2mmarin/work/sawteeth/sawteeth_64862.mat', time_start = 0.05)




