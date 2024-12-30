# Populating CoNekT Grasses with scripts

## About the scripts

There are currently two categories of scripts in the pipeline, reflecting the original organization of the admin panel by Dr. Sebastian Proost (CoNekT).

### Add scripts

#### Add Taxonomy (GTDB, SILVA, GreenGenes)

Currently, SILVA, GreenGenes and GTDB databases can be added to CoNekT Grasses Microbiome as shown here:

```bash
./add_taxonomy.py --silva_taxonomy_file /path/to/silva/138/tax_slv_lsu_138.1.txt --silva_release 138.1 --gg_taxonomy_file /path/to/gg_13_5/gg_13_5_taxonomy.txt --gg_release 13.5 --gtdb_taxonomy_file /path/to/gtdb/214/bac120_taxonomy_r214.tsv --gtdb_release 214 --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db
```

 * Add Functional Data (InterPro, Gene Ontology, CAZymes)
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
 