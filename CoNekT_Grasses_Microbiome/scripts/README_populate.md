# Populating CoNekT Grasses with NextFlow

## Setup of the NextFlow pipeline

Usually, it is necessary just to follow the steps for setting up described [on Nextflow official website](https://www.nextflow.io/).

For `nextflow version 24.10.0.5928`, which is currently being used (Ubuntu 22.04.5 LTS on a Intel® Xeon(R) CPU E5-1620 v3 @ 3.50GHz × 8):

```bash
curl -s https://get.nextflow.io | bash 
```


## Running the NextFlow pipeline


## About the scripts

There are currently two categories of scripts in the pipeline, reflecting the original organization of the admin panel by Dr. Sebastian Proost (CoNekT).

### Add

 * Add Functional Data (InterPro, Gene Ontology, CAZymes)
 * Add Taxonomy (GTDB, NCBI, SILVA, GreenGenes)
 * Add Ontology (PO, PECO and ENVO)

 * Add Species
 * Add description associated to species sequences
 * Add GO annotation for species
 * Add InterPro annotation for species
 * Add CAZyme annotation for species

 * Add samples

 * Add OTUs for species
 * Add OTU Classification (GTDB is mandatory; additional classification is optional)
 * Add OTU profiles

 * Add expression profiles

 * Add PCA to study
 * Add cross-correlations to study
 * Add GO enrichment to cross-correlated genes in a study

### Build

 * Create study
 * Compute microbiome specificity for study
 