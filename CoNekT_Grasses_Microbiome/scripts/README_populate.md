# Populating CoNekT Grasses with scripts

## About the scripts

There are currently two categories of scripts in the pipeline, reflecting the original organization of the admin panel by Dr. Sebastian Proost (CoNekT).

### Add scripts

#### Add Taxonomy


Currently, SILVA, GreenGenes and GTDB databases can be added to CoNekT Grasses Microbiome as shown here:

```bash
./add_taxonomy.py --silva_taxonomy_file /path/to/silva/138/tax_slv_lsu_138.1.txt --silva_release 138.1 --gg_taxonomy_file /path/to/gg_13_5/gg_13_5_taxonomy.txt --gg_release 13.5 --gtdb_taxonomy_file /path/to/gtdb/214/bac120_taxonomy_r214.tsv --gtdb_release 214 --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db
```

#### Add Functional Data


Currently, InterPro, Gene Ontology and CAZymes databases can be added to CoNekT Grasses Microbiome as shown here:

```bash
./add_functional_data.py --interpro_xml /path/to/FunctionalData/interpro.xml --gene_ontology_obo /path/to/FunctionalData/go.obo --cazyme /path/to/FunctionalData/CAZyDB.07302020.fam-activities.txt --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db
```

#### Add Ontology


Currently, Plant Ontology (PO), Plant Experimental Conditions Ontology (PECO) and Environment Ontology (ENVO) can be added to CoNekT Grasses Microbiome as shown here:

```bash
./add_ontologies.py --plant_ontology /path/to/Ontology/plant-ontology.txt --plant_e_c_ontology /path/to/Ontology/peco.tsv --envo /path/to/Ontology/envo_09012024.txt --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db
```

#### Add Species


For adding species to the database it is necessary to create a fie following this template (information separated by tabulation):

```bash
#Species_name   Code    Source  Genome_Transcriptome_version    DOI     CDS_file        RNA_file
Zea mays        Zma     Phytozome       Zmays_Zm_B73_REFERENCE_NAM_5_0_55       10.1126/science.abg5289 /path/to/Maize/Zma_cds.fa      /path/to/Maize/Zma_rnas.fa
```

Running the script:

```bash
./add_species.py --input_table /path/to/species_info.tsv --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db
```

#### Add description associated to species sequences


```bash
./add_gene_descriptions.py --species_code Zma --gene_descriptions /path/to/Maize/Zma_cds_descriptions.txt --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db
```

#### Add GO annotation for species


```bash
./add_go.py --species_code Zma --go_tsv /path/to/Maize/Zma_gos.tsv --annotation_source "GOs from InterProScan" --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db
```

#### Add InterPro annotation for species


```bash
./add_interproscan.py --interproscan_tsv /path/to/Maize/Zma_interproscan.tsv --species_code Zma --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db
```

#### Add CAZyme annotation for species



#### Add samples for species


```bash
./add_samples.py --species_code Zma --sample_annotation /path/to/Maize/Zma_sample_annotation.txt --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db
```

#### Add OTUs

```bash
 ./add_otus.py --literature_doi "10.1094/PBIOMES-02-18-0008-R" --amplicon_marker 16S --primer_pair "515F-1401R" --method_description "Brief description of the method used to generate OTUs" --clustering_method open_reference --clustering_algorithm qiime1 --clustering_threshold 0.97 --clustering_reference_db greengenes --clustering_reference_db_release 13_5 --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db --fasta_file /path/to/Maize/rep_set_conekt.fna
```

#### Add OTU Classification (GTDB is mandatory)




### Build scripts

#### Build study


Before adding expression and abundance data, it is necessary to create a study.

```bash
./create_study.py --species_code Zma --study_name "Integration of Maize Microbiome and Transcriptome in leaves" --study_description "Integration of Maize Microbiome and Transcriptome in leaves to understand the role of microbiome in plant transcriptome" --study_type expression_metataxonomics --krona_file /home/santosrac/Repositories/conekt_grasses_microbiome/CoNekT_Grasses_Microbiome/tests/data/microbiome_data/otus/text.krona.html --db_admin conekt_microbiome_admin --db_name conekt_microbiome_db
```





 * Add OTU profiles

 * Add expression profiles

 * Add PCA to study
 * Add cross-correlations to study
 * Add GO enrichment to cross-correlated genes in a study

 * Compute microbiome specificity for study
 