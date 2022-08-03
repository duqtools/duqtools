import os
import numpy as np
import matplotlib.pyplot as plt
import compare_im_runs
import prepare_im_input


'''
I am fairly sure this is not a nice way to do this, but I'll think of a better way later
'''

class CompareImRunsArguments:
    def __init__(
        self,
        backend = "mdsplus",
        database = None,
        shot = None,
        run = None,
        user = None,
        version = 3,
        time_begin = None,
        time_end = None,
        time_out = None,
        signal = None,
        source = ["total"],
        transport = ['transport_solver'],
        steady_state = False,
        show_plot = False,
        plot_uniform_basis = False,
        analyze_traces = None,
        analyze_profiles = None,
        change_sign = False,
        multi_var_function = None
    ):

        self.backend = backend
        self.database = database
        self.shot = shot
        self.run = run
        self.signal = signal
        self.version = version
        self.time_begin = time_begin
        self.time_end = time_end
        self.time_out = time_out
        self.user = user
        if not user:
            self.user = [os.getenv("USER")]
        self.source = source
        self.transport = transport
        self.steady_state = steady_state
        self.show_plot = show_plot
        self.plot_uniform_basis = plot_uniform_basis
        self.analyze_traces = analyze_traces
        self.analyze_profiles = analyze_profiles
        self.change_sign = change_sign
        self.multi_var_function = multi_var_function


def get_error(shot, run_input, run_output, signal, db = 'tcv'):

    # The time compared is the time of the simulation. Still on the experiment time array
    summary = prepare_im_input.open_and_get_summary(db, shot, run_output)
    time_begin, time_end = min(summary.time), max(summary.time)

    # Temporary hopefully. Only a few signals need to change sign. Listing them here
    change_sign = False
    if signal == 'summary.global_quantities.v_loop.value':
        summary_input = prepare_im_input.open_and_get_summary(db, shot, run_input)
        average_input = np.average(summary_input.global_quantities.v_loop.value)
        average_output = np.average(summary.global_quantities.v_loop.value)
        if np.sign(average_input) != np.sign(average_output):
            change_sign = True

    if signal == 'core_profiles.profiles_1d[].q':
        core_profiles_input = prepare_im_input.open_and_get_core_profiles(db, shot, run_input)
        core_profiles_output = prepare_im_input.open_and_get_core_profiles(db, shot, run_output)
        average_input = np.average(core_profiles_input.profiles_1d[0].q)
        average_output = np.average(core_profiles_output.profiles_1d[0].q)
        if np.sign(average_input) != np.sign(average_output):
            change_sign = True


    args = CompareImRunsArguments(
        database = [db],
        shot = [shot],
        run = [run_input,run_output],
        time_begin = time_begin,
        time_end = time_end,
        signal = [signal],
        change_sign = change_sign,
        show_plot = False
    )

    error_signal = compare_im_runs.main(args)

    return(error_signal)


def plot_errors(filename, signal_list):

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

    print(ax)
    #exit()


    for isignal, signal in enumerate(signal_list):
        # Needed for aoutoformatting
        icolumns = int(isignal/num_columns)
        iraws = isignal % num_columns

        print(icolumns, iraws)

        labels = shot_list
        x = np.arange(len(labels))  # the label locations
        width = 1/(num_run_series+1)  # the width of the bars

        for run_serie in range(num_run_series):
            errors = []

            for shot, run_input, run_output in zip(shot_list, run_input_list, run_output_list[:,run_serie]):
                errors.append(get_error(shot, run_input, run_output, signal)[0])

            rects = ax[icolumns][iraws].bar(x - width + width/num_run_series + run_serie*width, errors, width, label=labels_plot[run_serie])
        
            #ax[isignal].bar_label(rects, padding=3)
            #ax[isignal].bar_label(rects)

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax[icolumns][iraws].set_ylabel('Errors')
        ax[icolumns][iraws].set_title(signal)
        ax[icolumns][iraws].set_xticks(x, labels)
        ax[icolumns][iraws].legend()

        fig.tight_layout()

    plt.show()


if __name__ == "__main__":
    #plot_errors('runs_list.txt', ['summary.global_quantities.v_loop.value'])
    #plot_errors('runs_list.txt', ['summary.global_quantities.v_loop.value', 'core_profiles.profiles_1d[].q'])
    #plot_errors('runs_list.txt', ['summary.global_quantities.v_loop.value', 'core_profiles.profiles_1d[].q', 'summary.global_quantities.li.value'])
    plot_errors('runs_list.txt', ['summary.global_quantities.v_loop.value', 'core_profiles.profiles_1d[].q', 'summary.global_quantities.li.value', 'summary.global_quantities.beta_pol.value'])



