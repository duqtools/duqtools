# Dashboard

The dash subcommand opens a dashboard to explore the results of the UQ runs.

This requires duqtools to be installed with additional dependencies:

`pip install duqtools[dash]`

or, when installing the development version:

`pip install -e .[dash]`

To run the command:

`duqtools dash`

Check out [the command-line interface](/command-line-interface/#dash) for more info on how to use this command.


## Data input

### `runs.yaml`

Duqtools stores all run metdata in a file named `runs.yaml`. By default, the dashboard tries to load all the output data specified in this file.

### From a CSV file

Alternatively, you can import data by the IMAS handle from a CSV file.

The CSV file must contain the columns: `user`, `db`, `shot`, and `run`.
The index is an arbitrary name for each row.

For example:

```csv title="data.csv"
,user,db,shot,run
name_1,g2ssmee,jet,94875,8100
name_2,g2ssmee,jet,94875,8101
name_3,g2ssmee,jet,94875,8102
name_4,g2ssmee,jet,94875,8103
name_5,g2ssmee,jet,94875,8104
```
