# Installing IMASPy


```console
git clone https://git.iter.org/scm/imas/imaspy.git
cd imaspy
```

You need an `IDSDef.xml`, this one can be zipped and moved to:

```
./data-dictionary/IDSDEF.zip
```

Note: The data dictionary on Gateway can be found here:
`/gw/swimas/core/IMAS/3.34.0/AL/4.9.3/include/IDSDef.xml`

Install using:

```
pip install -e .
```

Docs

```console
cd docs
pip install -r ../requirements_docs.txt
make build
```
