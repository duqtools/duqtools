[Click here](../variables.md) for more information on the variables handling in *duqtools*.

## Definition

{{ schema_JettoVariableModel['description'] }}

{% for name, prop in schema_JettoVariableModel['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

The `lookup` field is defined by a so-called Jetto Variable, which maps to one or more locations in the jetto system configs (e.g., `jetto.jset`, or `jetti.in`).

{{ schema_JettoVar['description'] }}

{% for name, prop in schema_JettoVar['properties'].items() %}
`{{ name }}`
: {{ prop['description'] }}
{% endfor %}

The exact fields to write to are defined under the `keys` section, which takes the `file` to write to, the `section` (if applicable) and `field` the variable is mapped to.

Example:

```yaml title="duqtools.yaml"
extra_variables:
- name: major_radius
  type: jetto-variable
  lookup:
    name: major_radius
    doc: Reference major radius (R0)
    type: float
    keys:
    - field: EquilEscoRefPanel.refMajorRadius
      file: jetto.jset
    - field: RMJ
      file: jetto.in
      section: NLIST1
```

## Default variables

{% for name, var_group in variable_groups.items() %}
### {{ name }}s

{% for var in var_group %}

#### {{ var.name }}
```yaml
{{ var | to_yaml_str }}
```

{% endfor %}
{% endfor %}
