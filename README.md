# CoNekT Metataxonomics

## Description


CoNekT Metataxonomics derives from [CoNekT Grasses Microbiome](https://github.com/SantosRAC/conekt_grasses_microbiome) that, in turn, was built based on [CoNekT](https://github.com/sepro/conekt) [(Proost & Mutwil, 2018)](https://academic.oup.com/nar/article/46/W1/W133/4990637).


CoNekT Metataxonomics includes only metataxonomics datasets and is still under initial planning.

## Setting up the environment

Virtual env must be installed:

```bash
sudo apt install python3.10-venv python3.10-dev
pip3 install virtualenv
```

Creating and activating

```bash
virtualenv --python=python3.10 CoNekT_Grasses_Microbiome
# virtualenv creates a .gitignore file we want to delete, since it ignores all changes in repository
rm CoNekT_Grasses_Microbiome/.gitignore
source CoNekT_Grasses_Microbiome/bin/activate
pip install -r requirements.txt
```

## Building Sphinx documentation


Documentation can be generated using Sphinx.

To generate the documentation, run:

```bash
cd CoNekT_Grasses_Microbiome/docs/
sphinx-build -b html source/ build/
```

Note that we changed the default Sphinx builder to use the Markdown parser. This is done by adding the following line to `conf.py` file in the `CoNekT_Grasses_Microbiome/docs` folder:

```
extensions = ["myst_parser"]
```