# Introduction

Duqtools can also write directly to system config files. For jetto, duqtools uses [jetto-tools](https://pypi.org/project/jetto-tools/) to update the `jetto.jset` and `jetto.in`. These operations are handled by what we call 'systems'.

## Defining the Jetto System

The jetto system can be set by modifying `system` in the `duqtools.yaml`.

```yaml title="duqtools.yaml"
system:
  name: jetto
```

These options are available:

- `jetto` (alias for `jetto-v220922`)
- `jetto-v220922`

### Jetto-v220922

::: duqtools.systems.jetto.JettoSystemV220922
    options:
      show_root_toc_entry: false
      members: None
      show_bases: False

The Jetto system uses [jetto-pythontools](https://jintrac.gitlab.io/jetto-pythontools/) to write variables to the `jetto.jset`/`jetto.in` files.
These variables are defined in the [lookup.json](https://jintrac.gitlab.io/jetto-pythontools/lookup.html).
Duqtools includes its [own version](https://github.com/duqtools/duqtools/blob/main/src/duqtools/data/jetto_tools_lookup.json), but in case
you run into issues with future versions, you can specify your own by setting the environment variable `JETTO_LOOKUP`.
For example, `JETTO_LOOKUP=./my-jetto-lookup.json duqtools create`.

### Jetto output directory

If you do not specify anything in `duqtools.yaml`, the jetto output location depends on the location of `duqtools.yaml`:

1. If `duqtools.yaml` is **outside** `$JRUNS`: `$JRUNS/duqtools_experiment_xxx`
2. If `duqtools.yaml` is **inside** `$JRUNS`: Parent directory of `duqtools.yaml`

You can override the `$JRUNS` directory by setting the `jruns` variable. This must be a directory that `rjettov` can write to.

```yaml title="duqtools.yaml"
system:
  name: jetto
  jruns: /pfs/work/username/jetto/runs/
```
