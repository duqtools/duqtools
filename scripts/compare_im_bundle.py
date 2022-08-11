import os
import numpy as np
import matplotlib.pyplot as plt
import compare_im_runs
import prepare_im_input
import compare_im_exp

'''

Shows the comparison for multiple signals, multiple plots and multiple settings

Example of usage:

plot_errors('/afs/eufus.eu/user/g/user/mylist.txt', ['summary.global_quantities.v_loop.value', 'core_profiles.profiles_1d[].q', 'summary.global_quantities.li.value', 'te'], plot_type = 1, time_begin = 0.02, time_end = 0.1)


'''


exp_signal_list = ['te', 'ne', 'ti', 'ni']


def get_error(shot, run_input, run_output, signal, time_begin = None, time_end = None, db = 'tcv'):

    # The time compared is the time of the simulation. Still on the experiment time array
    summary = prepare_im_input.open_and_get_summary(db, shot, run_output)

    username = os.getenv("USER")
    userlist = [username]
    dblist = [db]
    shotlist = [shot]
    runlist = [run_input,run_output]
    # Exclude very fast equilibrium readjusting on the first few timesteps
    if not time_begin:
        time_begin = min(summary.time) + 0.01
    if not time_end:
        time_end = max(summary.time)
    signal = [signal]
    show_plot = False

    time_averages, time_error_averages, profile_error_averages = compare_im_runs.compare_runs(signal, dblist, shotlist, runlist, time_begin, userlist = userlist, time_end=time_end, plot=False, analyze=True, correct_sign=True, signal_operations=None)

    errors = []
    for signal in time_error_averages:
        for run_tag in time_error_averages[signal]:
            errors.append(time_error_averages[signal][run_tag])

    for signal in profile_error_averages:
        for run_tag in profile_error_averages[signal]:
            errors.append(profile_error_averages[signal][run_tag])

    return errors


def get_exp_error(shot, run_input, run_output, signal, time_begin = None, time_end = None, db = 'tcv'):

    summary = prepare_im_input.open_and_get_summary(db, shot, run_output)
    if not time_begin:
        time_begin = min(summary.time) + 0.01
    if not time_end:
        time_end = max(summary.time)

    return(compare_im_exp.plot_exp_vs_model(db, shot, run_input, run_output, time_begin, time_end, signals = [signal], verbose = 0))


def plot_errors(filename, signal_list, time_begin = None, time_end = None, plot_type = 1):

    file_runs = open(filename, 'r')
    lines = file_runs.readlines()
    shot_list, run_input_list, run_output_list = [], [], []
    labels_plot = lines[0].split(' ')
    for line in lines[1:]:
        shot, run_input, *runs_output = line.split(' ')
        shot_list.append(int(shot))
        run_input_list.append(int(run_input))
        # Want to compare multiple series of runs to check which one is better
        num_run_series = len(runs_output)
        for run_output in runs_output:
            run_output_list.append(int(run_output))

    run_output_list = np.asarray(run_output_list).reshape(len(lines)-1, num_run_series)

    # Pre deciding the structure of the plots with the various possibilities of len(signal_list)

    if len(signal_list) == 1:
        fig, ax = plt.subplots(1,1)
        ax, num_columns = [[ax]], 1
    elif len(signal_list) == 2:
        fig, ax = plt.subplots(1,2)
        ax, num_columns = [ax], 1
    elif len(signal_list) == 3:
        fig, ax = plt.subplots(1,3)
        ax, num_columns = [ax], 1
    elif len(signal_list) == 4:
        fig, ax = plt.subplots(2,2)
        num_columns = 2

    if plot_type == 1:
        for isignal, signal in enumerate(signal_list):
            # Needed for aoutoformatting
            icolumns = int(isignal/num_columns)
            iraws = isignal % num_columns

            labels = shot_list
            x = np.arange(len(labels))  # the label locations
            width = 1/(num_run_series+1)  # the width of the bars

            for run_serie in range(num_run_series):
                errors = []
                #if signal not in exp_signal_list:
                for shot, run_input, run_output in zip(shot_list, run_input_list, run_output_list[:,run_serie]):
                    if signal not in exp_signal_list:
                         errors.append(get_error(shot, run_input, run_output, signal, time_begin = time_begin, time_end = time_end)[0])
                    else:
                         errors.append(get_exp_error(shot, run_input, run_output, signal, time_begin = time_begin, time_end = time_end)[0])

                rects = ax[icolumns][iraws].bar(x - width + width/num_run_series + run_serie*width, errors, width, label=labels_plot[run_serie])

            # Add some text for labels, title and custom x-axis tick labels, etc.
            ax[icolumns][iraws].set_ylabel('Distance')
            ax[icolumns][iraws].set_title(signal)
            ax[icolumns][iraws].set_xticks(x, labels)
            ax[icolumns][iraws].legend()

            fig.tight_layout()

        plt.show()

    elif plot_type == 2:
        for isignal, signal in enumerate(signal_list):
            # Needed for aoutoformatting
            icolumns = int(isignal/num_columns)
            iraws = isignal % num_columns

            x = np.arange(num_run_series)  # the label locations
            width = 1/(len(shot_list)+1)  # the width of the bars

            for shot in range(len(shot_list)):
                errors = []
                for run_output in run_output_list[shot,:]:
                    if signal not in exp_signal_list:
                        errors.append(get_error(shot_list[shot], run_input_list[shot], run_output, signal, time_begin = time_begin, time_end = time_end)[0])
                    else:
                        errors.append(get_exp_error(shot_list[shot], run_input_list[shot], run_output, signal, time_begin = time_begin, time_end = time_end)[0])

                rects = ax[icolumns][iraws].bar(x - width + width/len(shot_list) + shot*width, errors, width, label=shot_list[shot])

            # Add some text for labels, title and custom x-axis tick labels, etc.
            ax[icolumns][iraws].set_ylabel('Distance')
            ax[icolumns][iraws].set_title(signal)
            ax[icolumns][iraws].set_xticks(x, labels_plot)
            ax[icolumns][iraws].legend()

            fig.tight_layout()

        plt.show()


if __name__ == "__main__":

    print('compare sets of runs')

