from __future__ import annotations

import numpy as np


class nested_val:
    val = np.array([123])


class profile_t0:
    grid = np.arange(10.0) * 1
    variable = grid**2
    val = 1
    empty = np.array([])


class profile_t1:
    grid = np.arange(10.0) * 2
    variable = grid**2
    val = 2
    empty = np.array([])


class profile_t2:
    grid = np.arange(10.0) * 3
    variable = grid**2
    val = 3
    empty = np.array([])


class nested_profile_t0:
    data = profile_t0


class nested_profile_t1:
    data = profile_t1


class nested_profile_t2:
    data = profile_t2


class ion_1:
    variable = np.arange(25.0).reshape(5, 5) * 1


class ion_2:
    variable = np.arange(25.0).reshape(5, 5) * 2


class ion_3:
    variable = np.arange(25.0).reshape(5, 5) * 3


class arr_t0:
    grid = np.arange(25.0).reshape(5, 5) * 1
    variable = grid**1
    ions = [ion_1, ion_2, ion_3]


class arr_t1:
    grid = np.arange(25.0).reshape(5, 5) * 2
    variable = grid**2
    ions = [ion_1, ion_2, ion_3]


class arr_t2:
    grid = np.arange(25.0).reshape(5, 5) * 3
    variable = grid**3
    ions = [ion_1, ion_2, ion_3]


class nested_arr_t0:
    data = arr_t0


class nested_arr_t1:
    data = arr_t1


class nested_arr_t2:
    data = arr_t2


class Sample:
    profiles_1d = [profile_t0, profile_t1, profile_t2]
    nested_profiles_1d = [
        nested_profile_t0, nested_profile_t1, nested_profile_t2
    ]

    profiles_2d = [arr_t0, arr_t1, arr_t2]
    nested_profiles_2d = [nested_arr_t0, nested_arr_t1, nested_arr_t2]

    single_val = np.array([123])
    nested_single_val = nested_val

    single_profile_1d = profile_t0
    nested_single_profile_1d = nested_profile_t0

    single_profile_2d = arr_t0
    nested_single_profile_2d = nested_arr_t0

    time = np.array((23, 24, 25))
