[Click here](../variables.md) for more information on the variables handling in *duqtools*.

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
