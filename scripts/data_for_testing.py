import numpy as np


class nested_val:
    val = np.array([123])


class profile_t0:
    grid = np.arange(10) * 1.1
    variable = grid**1.1
    variable_error_upper = np.array([])
    val = 1


class profile_t1:
    grid = np.arange(10) * 1.2
    variable = grid**1.2
    variable_error_upper = np.array([])
    val = 2


class profile_t2:
    grid = np.arange(10) * 1.3
    variable = grid**1.3
    variable_error_upper = np.array([])
    val = 3


class nested_profile_t0:
    data = profile_t0


class nested_profile_t1:
    data = profile_t1


class nested_profile_t2:
    data = profile_t2


class arr_t0:
    grid = np.arange(25).reshape(5, 5) * 1.1
    variable = grid**1.1
    variable_error_upper = np.array([])


class arr_t1:
    grid = np.arange(25).reshape(5, 5) * 1.2
    variable = grid**1.2
    variable_error_upper = np.array([])


class arr_t2:
    grid = np.arange(25).reshape(5, 5) * 1.3
    variable = grid**1.3
    variable_error_upper = np.array([])


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
