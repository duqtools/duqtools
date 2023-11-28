"""Handle = H5Handle(path='/afs/eufus.eu/user/g/g2ssmee/imas2xarray/data')

dataset = handle.get_variables(variables=(x_var, y_var, time_var))
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import h5py

from ._lookup import var_lookup
from ._mapping import IDSMapping
from ._rebase import squash_placeholders

if TYPE_CHECKING:
    import xarray as xr

    from duqtools.imas2xarray import IDSVariableModel


class H5Handle:

    def __init__(self, path: Path):
        self.path = Path(path)

    def get(self, ids: str = 'core_profiles') -> IDSMapping:
        """Map the data to a dict-like structure.

        Parameters
        ----------
        ids : str, optional
            Name of profiles to open

        Returns
        -------
        IDSMapping
        """
        data_file = (self.path / ids).with_suffix('.h5')
        assert data_file.exists()

        raw_data = h5py.File(data_file, 'r')[ids]

        # TODO: Add missing interface between hdf5 and IDSMapping

        return IDSMapping(raw_data)

    def get_all_variables(
        self,
        extra_variables: Sequence[IDSVariableModel] = [],
        squash: bool = True,
        ids: str = 'core_profiles',
        **kwargs,
    ) -> xr.Dataset:
        """Get all variables that duqtools knows of from selected ids from the
        dataset.

        This function looks up the data location from the
        `duqtools.config.var_lookup` table

        Parameters
        ----------
        variables : Sequence[IDSVariableModel]
            Extra variables to load in addition to the ones known by duqtools.
        squash : bool
            Squash placeholder variables

        Returns
        -------
        ds : xarray
            The data in `xarray` format.
        **kwargs
            These keyword arguments are passed to `IDSMapping.to_xarray()`

        Raises
        ------
        ValueError
            When variables are from multiple IDSs.
        """

        idsvar_lookup = var_lookup.filter_ids(ids)
        variables = list(
            set(list(extra_variables) + list(idsvar_lookup.keys())))
        return self.get_variables(variables,
                                  squash,
                                  empty_var_ok=True,
                                  **kwargs)

    def get_variables(
        self,
        variables: Sequence[str | IDSVariableModel],
        squash: bool = True,
        **kwargs,
    ) -> xr.Dataset:
        """Get variables from data set.

        This function looks up the data location from the
        `duqtools.config.var_lookup` table, and returns

        Parameters
        ----------
        variables : Sequence[Union[str, IDSVariableModel]]
            Variable names of the data to load.
        squash : bool
            Squash placeholder variables

        Returns
        -------
        ds : xarray
            The data in `xarray` format.
        **kwargs
            These keyword arguments are passed to `IDSMapping.to_xarray()`

        Raises
        ------
        ValueError
            When variables are from multiple IDSs.
        """
        var_models = var_lookup.lookup(variables)

        idss = {var.ids for var in var_models}

        if len(idss) > 1:
            raise ValueError(
                f'All variables must belong to the same IDS, got {idss}')

        ids = var_models[0].ids

        data_map = self.get(ids)

        ds = data_map.to_xarray(variables=var_models, **kwargs)

        if squash:
            ds = squash_placeholders(ds)

        return ds
