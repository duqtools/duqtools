import os
import sys
import re
import copy
import numpy as np
import math
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
#import matplotlib
#matplotlib.use('Qt5Agg')
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation

from IPython import display
import argparse

import imas

from compare_im_runs import *
from prepare_im_input import open_and_get_core_profiles


def plot_exp_vs_model(db, shot, run_exp, run_model, time_begin, time_end, signals = ['te', 'ne', 'ti', 'ni'], verbose = False):

    variable_names = {}
    if 'te' in signals:
        variable_names['electron temperature'] = [
        'core_profiles.profiles_1d[].electrons.temperature_fit.measured',
        'core_profiles.profiles_1d[].electrons.temperature_fit.measured_error_upper',
        'core_profiles.profiles_1d[].electrons.temperature'
    ]
    if 'ne' in signals:
        variable_names['electron density'] = [
        'core_profiles.profiles_1d[].electrons.density_fit.measured',
        'core_profiles.profiles_1d[].electrons.density_fit.measured_error_upper',
        'core_profiles.profiles_1d[].electrons.density'
    ]
    if 'ti' in signals:
        variable_names['ion temperature'] = [
        'core_profiles.profiles_1d[].t_i_average_fit.measured',
        'core_profiles.profiles_1d[].t_i_average_fit.measured_error_upper',
        'core_profiles.profiles_1d[].t_i_average'
    ]
    if 'ni' in signals:
        variable_names['impurity density'] = [
        'core_profiles.profiles_1d[].ion[1].density_fit.measured',
        'core_profiles.profiles_1d[].ion[1].density_fit.measured_error_upper',
        'core_profiles.profiles_1d[].ion[1].density'
    ]

    core_profiles_exp = open_and_get_core_profiles(db, shot, run_exp)
    core_profiles_model = open_and_get_core_profiles(db, shot, run_model)

    t_cxrs = []

    for profile in core_profiles_exp.profiles_1d:
        t_cxrs.append(profile.t_i_average_fit.time_measurement)

    t_cxrs = np.asarray(t_cxrs).flatten()
    t_cxrs = t_cxrs[np.where(t_cxrs < time_begin, False, True)]
    t_cxrs = t_cxrs[np.where(t_cxrs > time_end, False, True)]

    for variable in variable_names:
        exp_data = get_onesig(core_profiles_exp,variable_names[variable][0],time_begin,time_end=time_end)
        errorbar = get_onesig(core_profiles_exp,variable_names[variable][1],time_begin,time_end=time_end)

        for time in exp_data:

            # Clean data that are not in the core
            exp_data[time]['y'] = exp_data[time]['y'][np.where(exp_data[time]['x'] > 1, False, True)]
            errorbar[time]['y'] = errorbar[time]['y'][np.where(exp_data[time]['x'] > 1, False, True)]
            errorbar[time]['x'] = errorbar[time]['x'][np.where(exp_data[time]['x'] > 1, False, True)]
            exp_data[time]['x'] = exp_data[time]['x'][np.where(exp_data[time]['x'] > 1, False, True)]

            # Clean experimental data that were not filled properly
            exp_data[time]['x'] = exp_data[time]['x'][np.where(exp_data[time]['y'] < -0, False, True)]
            errorbar[time]['y'] = errorbar[time]['y'][np.where(exp_data[time]['y'] < -0, False, True)]
            errorbar[time]['x'] = errorbar[time]['x'][np.where(exp_data[time]['y'] < -0, False, True)]
            exp_data[time]['y'] = exp_data[time]['y'][np.where(exp_data[time]['y'] < -0, False, True)]

            # Clean experimental data that are filled with nans
            exp_data[time]['x'] = exp_data[time]['x'][np.where(np.isnan(exp_data[time]['y']), False, True)]
            errorbar[time]['y'] = errorbar[time]['y'][np.where(np.isnan(exp_data[time]['y']), False, True)]
            errorbar[time]['x'] = errorbar[time]['x'][np.where(np.isnan(exp_data[time]['y']), False, True)]
            exp_data[time]['y'] = exp_data[time]['y'][np.where(np.isnan(exp_data[time]['y']), False, True)]

        # Hacky. But well...
        time_vector_exp = np.asarray(list(exp_data.keys()))

        if variable == 'ion temperature' or variable == 'impurity density':
            exp_data_new, errorbar_new = {}, {}
            time_vector_exp = np.asarray(list(exp_data.keys()))
            for time_cxrs in t_cxrs:
                time_closest = time_vector_exp[np.abs(time_vector_exp - time_cxrs).argmin(0)]
                exp_data_new[time_cxrs] = exp_data[time_closest]
                errorbar_new[time_cxrs] = errorbar[time_closest]

            exp_data = exp_data_new
            errorbar = errorbar_new
            time_vector_exp = np.unique(t_cxrs)

            # Errors are stored differently. I think this is the right way and errors should be like this also for te and ne...
            for time in time_vector_exp:
                errorbar[time]['y'] = errorbar[time]['y'] - exp_data[time]['y']


        fit = get_onesig(core_profiles_model,variable_names[variable][2],time_begin,time_end=time_end)
        time_vector_fit = np.asarray(list(fit.keys()))

        # For every timelisce in experiments, remap all the fits on that x and then interpolate. It is necessary if the x coordinate changes in time
        ytable_final = []
        for time_exp in time_vector_exp:
            ytable_temp = None
            for time_fit in time_vector_fit:
                y_new = fit_and_substitute(fit[time_fit]["x"], exp_data[time_exp]["x"], fit[time_fit]["y"])
                ytable_temp = np.vstack((ytable_temp, y_new)) if ytable_temp is not None else np.atleast_2d(y_new)

            ytable_temp.reshape(time_vector_fit.shape[0], exp_data[time_exp]["x"].shape[0])

            ytable_new = None
            for ii in range(exp_data[time_exp]['x'].shape[0]):
                y_new = fit_and_substitute(time_vector_fit, time_exp, ytable_temp[:, ii])
                ytable_new = np.vstack((ytable_new, y_new)) if ytable_new is not None else np.atleast_2d(y_new)

            ytable_final.append(ytable_new)

        #fit_values, exp_values = [], []
        #for itime, time_exp in enumerate(time_vector_exp):
        #    fit_values.append(ytable_final[itime][5])
        #    exp_values.append(exp_data[time_exp]['y'][5])


        #fit_values = np.asarray(fit_values).flatten()
        #exp_values = np.asarray(exp_values).flatten()

        if verbose:
            for i, time in enumerate(exp_data):

                plt.errorbar(exp_data[time]['x'], exp_data[time]['y'], yerr=errorbar[time]['y'], linestyle = ' ', label = 'experiment')
                plt.plot(exp_data[time]['x'], ytable_final[i], label = 'fit/model')
                plt.title(str(time))
                plt.legend()
                plt.show()

        # Calculate error
        error_time = []
        for i, time in enumerate(exp_data):
            error_time_space = []
            for y_fit, y_exp, error_point in zip(ytable_final[i], exp_data[time]['y'], errorbar[time]['y']):
                error_time_space.append(abs(y_fit[0] - y_exp)/error_point)

            if verbose:
                plt.plot(exp_data[time]['x'], error_time_space, 'bo', label = 'Agreement')
                plt.title(str(time))
                plt.legend()
                plt.show()

            error_time.append(sum(error_time_space)/len(exp_data[time]['y']))

        plt.plot(time_vector_exp, error_time, label = 'Agreement')
        plt.title(variable)
        plt.legend()
        plt.show()

        error_variable = sum(error_time)/len(exp_data)

        print('The error for ' + variable + ' is ' + str(error_variable))

if __name__ == "__main__":
    plot_exp_vs_model('tcv', 64965, 5, 517, 0.05, 0.15, signals = ['ti', 'ni'], verbose = True)
    #plot_exp_vs_model('tcv', 64965, 5, 517, 0.05, 0.15, verbose = True)
    #plot_exp_vs_model('tcv', 56653, 1, 200, 0.05, 0.15, verbose = True)


