# CoNekT Grasses Microbiome

## Description


CoNekT Grasses Microbiome derives from [CoNekT Grasses](https://github.com/labbces/conekt_grasses) that, in turn, was built based on [CoNekT](https://github.com/sepro/conekt) [(Proost & Mutwil, 2018)](https://academic.oup.com/nar/article/46/W1/W133/4990637).


CoNekT Grasses Microbiome is under development in a collaboration between [LabBCES (SP, Brazil)](https://labbces.cena.usp.br/) and the [Wallace Lab (UGA, GA, USA)](https://wallacelab.uga.edu/), and is being led by [Dr. Renato Santos](https://santosrac.netlify.app/), under supervision of Prof. Dr. Diego M. Riaño-Pachón and Prof. Dr. Jason Wallace.

## Setting up the environment

Virtual env must be installed:

```bash
sudo apt install python3.8-venv python3.8-dev python3.8-distutils
pip3 install virtualenv
```

Creating and activating

```bash
virtualenv --python=python3.8 CoNekT_Grasses_Microbiome
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

Next steps:

 * Build the datatase
 * Add data to CoNekT Grasses Microbiome
 * Running tests

## Funding


 * [Sao Paulo Research Foundation (FAPESP)](https://fapesp.br/)
  * [Research Internship Abroad Process #2023/11133-3](https://bv.fapesp.br/en/bolsas/212537/integrating-metataxonomics-and-host-transcriptomics-data-in-maize/)


## Licenses

 * [LabBCES LICENSE](LICENSE)
 * [Original CoNekT license (Dr. Sebastian Proost)](LICENSE_CoNekT.md)