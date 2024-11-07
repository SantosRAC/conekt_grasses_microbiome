# Populating CoNekT Grasses with NextFlow

## Setup of the NextFlow pipeline

Usually, it is necessary just to follow the steps for setting up described [on Nextflow official website](https://www.nextflow.io/).

For `nextflow version 24.10.0.5928`, which is currently being used (Ubuntu 22.04.5 LTS on a Intel® Xeon(R) CPU E5-1620 v3 @ 3.50GHz × 8):

```bash
curl -s https://get.nextflow.io | bash 
```

## Setting up the MariaDB database

Usually, we will want to separate the database used in production from the one we fill with new data (especially during development stages). Here's a summary of how to setup this database for filling with data using the NextFlow pipeline.

Steps to create the new/parallel database `conekt_microbiome_dev_db` are described below. Commands must be executed with admin permission. Also, ignore the `CREATE USER` if it already existed.

```sql
CREATE USER conekt_microbiome_admin@localhost IDENTIFIED BY 'E,~5*;{9f{p2VGp^';
CREATE DATABASE conekt_microbiome_dev_db CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_unicode_ci';
GRANT INDEX, CREATE, DROP, SELECT, UPDATE, DELETE, ALTER, EXECUTE, INSERT on conekt_microbiome_dev_db.* TO conekt_microbiome_admin@localhost;
GRANT FILE on *.* TO conekt_microbiome_admin@localhost;
FLUSH PRIVILEGES;
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
 