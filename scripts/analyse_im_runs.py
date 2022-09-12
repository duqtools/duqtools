#!/usr/bin/env python
import os
import sys
import re
import copy
import numpy as np
import argparse
from prepare_im_input import open_and_get_summary

import imas

def input():

    parser = argparse.ArgumentParser(
        description=
"""Compute interesting values from JINTRAC IDS outputs. Preliminary version, created by A. Ho.\n
---
Examples:\n
python analyse_im_runs.py -u g2aho -d jet -s 94875 -r 1 -t jdifftime\n
---
""", 
    epilog="", 
    formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("--backend",     "-b",            type=str, help="Backend with which to access data", default="mdsplus", choices=["mdsplus", "hdf5"])
    parser.add_argument("--database",    "-d", nargs='+', type=str, help="Database/machine name(s) in which the data is stored", default=None)
    parser.add_argument("--shot",        "-s", nargs='+', type=int, help="Shot number(s) in which the data is stored", default=None)
    parser.add_argument("--run",         "-r", nargs='+', type=int, help="Run number(s) in which the data is stored", default=None)
    parser.add_argument("--user",        "-u", nargs='*', type=str, help="Username(s) with the data in his/her imasdb", default=[os.getenv("USER")])
    parser.add_argument("--version",     "-v",            type=str, help="UAL version", default="3")
    parser.add_argument("--type",        "-t",            type=str, help="Type of analysis to perform", default="jdifftime", choices=["jdifftime"])
    parser.add_argument("--change_sign",       action='store_true', help="Allows to change the sign of the output if it is not the same in the HFPS and in the IDS", default=False)

    args = parser.parse_args()
    return args

def main():
    args = input()
    db = args.database
    shot = args.shot
    run = args.run
    user = args.user
    n_db = len(db)
    n_shot = len(shot)
    n_run = len(run)
    n_user = len(user)
    if n_db != n_shot or n_db != n_run or n_db != n_user:
        maxn = int(np.nanmax([n_db, n_shot, n_run, n_user]))
        if n_db == 1 and maxn > 1:
            db = db * maxn
        if n_shot == 1 and maxn > 1:
            shot = shot * maxn
        if n_run == 1 and maxn > 1:
            run = run * maxn
        if n_user == 1 and maxn > 1:
            user = user * maxn
    n_db = len(db)
    n_shot = len(shot)
    n_run = len(run)
    n_user = len(user)
    targets = [(db[0], shot[0], run[0], user[0])]
    if n_db != n_shot or n_db != n_run or n_db != n_user:
        minn = int(np.nanmin([n_db, n_shot, n_run, n_user]))
        if minn > 1:
            targets = zip(db[:minn], shot[:minn], run[:minn], user[:minn])

    result = None
    if args.type == 'jdifftime':
        for item in targets:
            sum_ids = open_and_get_summary(item[0], item[1], item[2], item[3], args.backend)
            mu0 = 1.25663706e-6
            kfactor = 0.05 # This is heuristic from [D.R. Mikkelsen, Phys. Fluids B 1989]
            current_diffusion_time = kfactor * 2.0 * mu0 * np.abs(sum_ids.global_quantities.ip.value * sum_ids.global_quantities.r0.value / sum_ids.global_quantities.v_loop.value)
            if isinstance(current_diffusion_time, np.ndarray):
                current_diffusion_time_error = float(np.std(current_diffusion_time))
                current_diffusion_time = float(np.average(current_diffusion_time))
#                print("error = %20.6f" % (current_diffusion_time_error))
            this = "Current diffusion time: %20.6f" % (current_diffusion_time)
            result = this if result is None else result + "\n" + this
    if result is None:
        result = "Script failed!"
    print(result)

if __name__ == "__main__":
    main()
