# Create

The create subcommand creates the UQ run files.

To run the command:

`duqtools create`

Check out [the command-line interface](../command-line-interface.md#create) for more info on how to use this command.

<script id="asciicast-p4FXHwy5yS9u9n1WQexvs7g1h" src="https://asciinema.org/a/p4FXHwy5yS9u9n1WQexvs7g1h.js" async></script>

## The `create` config

{{ schema_CreateConfigModel['description'] }}

{% for name, prop in schema_CreateConfigModel['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
create:
  runs_dir: /pfs/work/username/jetto/runs/run_1
  template: /pfs/work/username/jetto/runs/duqtools_template
  operations:
    - variable: t_start
      operator: copyto
      value: 2.875
    - variable: t_end
      operator: copyto
      value: 2.885
  dimensions:
    - variable: t_e
      operator: multiply
      values: [0.9, 1.0, 1.1]
      scale_to_error: false
    - variable: zeff
      operator: multiply
      values: [0.9, 1.0, 1.1]
      scale_to_error: false
  sampler:
    method: latin-hypercube
    n_samples: 3
```


## Jetto output directory

If you do not specify anything, the jetto output location depends on the location of `duqtools.yaml`:

1. If `duqtools.yaml` is **outside** `$JRUNS`: `$JRUNS/duqtools_experiment_xxx`
2. If `duqtools.yaml` is **inside** `$JRUNS`: Parent directory of `duqtools.yaml`

You can override the `$JRUNS` directory by setting the `jruns` variable. This must be a directory that `rjettov` can write to.

```yaml title="duqtools.yaml"
system:
  name: jetto
  jruns: /pfs/work/username/jetto/runs/
```

You can modify the duqtools output directory via `runs_dir`:

```yaml title="duqtools.yaml"
runs_dir: my_experiment
```

## Specify the template data

By default the template IMAS data to modify is extracted from the path specified in the `template` field.

```yaml title="duqtools.yaml"
template: /pfs/work/username/jetto/runs/duqtools_template
```

In some cases, it may be useful to re-use the same set of model settings, but with different input data. If the `template_data` field is specified, these data will be used instead. To do so, specify `template_data` with the fields below:

{% for name, prop in schema_ImasBaseModel['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
template: /pfs/work/username/jetto/runs/duqtools_template
template_data:
  user: username
  db: jet
  shot: 91234
  run: 5
```


## Data location

{{ schema_DataLocation['description'] }}

{% for name, prop in schema_DataLocation['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
data:
  imasdb: test
  run_in_start_at: 7000
  run_out_start_at: 8000
```

## Samplers

Depending on the number of dimensions, a hypercube is constructed from which duqtools will select a number of entries. For a setup with 3 dimension of size $i$, $j$, $k$, a hypercube of $i\times j\times k$ elements will e constructed, where each element is a one of the combinations.

By default the entire hypercube is sampled:

```yaml title="duqtools.yaml"
sampler:
  method: cartesian-product
```

For smarter sampling, use one of the other methods: [`latin-hypercube`](https://en.wikipedia.org/wiki/Latin_hypercube_sampling), [`sobol`](https://en.wikipedia.org/wiki/Sobol_sequence), or [`halton`](https://en.wikipedia.org/wiki/Halton_sequence).
`n_samples` gives the number of samples to extract. For example:

```yaml title="duqtools.yaml"
sampler:
  method: latin-hypercube
  n_samples: 5
```

## Dimensions

These instructions operate on the template model. Note that these are compound operations, so they are expanded to fill the matrix with possible entries for data modifications (depending on the sampling method).

### Arithmetic operations

{{ schema_IDSOperationDim['description'] }}

{% for name, prop in schema_IDSOperationDim['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

For example:

```yaml title="duqtools.yaml"
variable: zeff
operator: add
values: [0.01, 0.02, 0.03]
```

will generate 3 entries, `zeff += 0.01`, `zeff += 0.02`, and `zeff += 0.03`.

```yaml title="duqtools.yaml"
variable: t_i_ave
operator: multiply
values: [1.1, 1.2, 1.3]
```

will generate another 3 entries, `t_i_ave *= 1.1`, `t_i_ave *= 1.2`, and `t_i_ave *= 1.3`.

With these 2 entries, the parameter hypercube would consist of 9 entries total (3 for `zeff`
times 3 for `t_i_ave`).
With the default `sampler: latin-hypercube`, this means 9 new data files will be written.

!!! note

    The python equivalent is essentially `np.<operator>(ids, value, out=ids)` for each of the given values.

!!! note

    If you want to copy all time ranges, you can use `path: profiles_1d/*/t_i_ave`. The `*` substring will
    duqtools to apply the operation to all available time slices.

#### Clipping profiles

Values can be clipped to a lower or upper bound by specifying `clip_min` or `clip_max`. This can be helpful to guard against unphysical values. The example below will clip the profile for Zeff at 1 (lower bound):

```yaml
variable: zeff
operator: multiply
values: [0.8, 0.9, 1.0, 1.1, 1.2]
clip_min: 1
```

#### Linear ramps

Before applying the operator, the given value can be ramped along the horizontal axis (rho) by specifying the `linear_ramp` keyword.

The two values represent the start and stop value of a linear ramp. For each value in `values`, the data at $\rho = 0$ are multiplied by `1 * value`, data at $\rho = 1$ are multiplied by `2 * value`. All values inbetween get multiplied based on a linear interpolation betwen those 2 values.

```yaml
variable: t_e
operator: multiply
values: [0.8, 1.0, 1.2]
linear_ramp: [1, 2]
```

#### Custom functions

If the standard operators are not suitable for your use-case, you can define your own functions using the `custom` operator.

This can be any custom Python code. Two variables are accessible. `data` corresponds to the variable data, and `value` to one of the specified values in the `values` field. The only restriction is that the output of the code *must* have the same dimensions as the input.

The example shows an implementation of `operator: multiply` with [lower and upper bounds](#clipping-profiles) using a custom function.

```yaml
variable: t_e
operator: custom
values: [0.8, 1.0, 1.2]
custom_code: 'np.clip(data * value, a_min=0, a_max=100)'
```


#### Using other variables as input

It is possible to specify other variables to use as input for your operation. This can be used to calculate a value of a variable with a `custom` operation which includes these variables. These variables are available in the `custom_code` as `var[<variable name>]`.

The example below sets all `t_i_ave` to some value calculated by dividing `t_i_ave_0` by `rho_tor_norm_0`

```yaml
extra_variables:
- name: rho_tor_norm_0
  ids: core_profiles
  path: profiles_1d/0/grid/rho_tor_norm
  dims: [time]
  type: IDS-variable
- name: t_i_ave_0
  ids: core_profiles
  path: profiles_1d/0/t_i_ave
  dims: [time]
  type: IDS-variable
create:
  dimensions:
    variable: t_i_ave
    operator: custom
    values: [1.0]
    input_variables:
      - "t_i_ave_0"
      - "rho_tor_norm_0"
    custom_code: 'var["t_i_ave_0"]/var["rho_tor_norm_0"]'
```

!!! note

  - If a variable that has been operated on earlier is specified as input, it will probably be the new value.
  - `input_variables` must not have multiple dimensions (so for IDS, no `*` operator in the path is allowed.


### Variables

To specify additional variables, you can use the `extra_variables` lookup file. The examples will use the `name` attribute to look up the location of the data. For example, `variable: zeff` will refer to the entry with `name: zeff`.

For more info about variables, see [here](../index#extra-variables).

### Value ranges

Although it is possible to specify value ranges explicitly in an operator, sometimes it may be easier to specify a range.

There are two ways to specify ranges in *duqtools*.

#### By number of samples

{{ schema_LinSpace['description'] }}

{% for name, prop in schema_LinSpace['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

This example generates a range from 0.7 to 1.3 with 10 steps:

```yaml title="duqtools.yaml"
variable: t_i_ave
operator: multiply
values:
  start: 0.7
  stop: 1.3
  num: 10
```

#### By stepsize

{{ schema_ARange['description'] }}

{% for name, prop in schema_ARange['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

This example generates a range from 0.7 to 1.3 with steps of 0.1:

```yaml title="duqtools.yaml"
variable: t_i_ave
operator: multiply
values:
  start: 0.7
  stop: 1.3
  step: 0.1
```

### Sampling between error bounds

From the data model convention, only the upper error node (`_error_upper`) should be filled in case of symmetrical error bars. If the lower error node (`_error_lower`) is also filled, *duqtools* will scale to the upper error for values larger than 0, and to the lower error for values smaller than 0.

The following example takes `t_e`, and generates a range from $-2\sigma$ to $+2\sigma$ with defined steps:

```yaml title="duqtools.yaml"
variable: t_e
operator: add
values: [-2, -1, 0, 1, 2]
scale_to_error: True
```

The following example takes `t_i_ave`, and generates a range from $-3\sigma$ to $+3\sigma$ with 10 equivalent steps:

```yaml title="duqtools.yaml"
variable: t_i_ave
operator: add
values:
  start: -3
  stop: 3
  num: 10
scale_to_error: True
```

!!! note

    When you specify a sigma range, make sure you use `add` as the operator. While the other operators are also supported, they do not make much sense in this context.

### Coupling Variables

It is possible to couple the sampling of two variables, simply add them as a single `List` entry to the configurations file:


```yaml title="duqtools.yaml"
-  - variable: t_start
     operator: copyto
     values: [0.1, 0.2, 0.3]
   - variable: t_end
     operator: copyto
     values: [1.1, 1.2, 1.3]
```  
