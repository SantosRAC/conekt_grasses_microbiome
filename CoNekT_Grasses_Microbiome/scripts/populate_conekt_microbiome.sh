#!/usr/bin/env bash

BASE_DIR=/home/santosrac/Repositories/conekt_grasses_microbiome
SCRIPTS_DIR=$BASE_DIR/CoNekT_Grasses_Microbiome/scripts
SPECIES_ARRAY=( Zma )
DATA_DIR=/home/renato/projects/uga_cena/conekt_grasses_microbiome
#SPECIES_TABLE=$DATA_DIR/Species/species_info.tsv

#Database credentials for CoNekT Grasses from file
#Expected variables: DB_ADMIN, DB_NAME and DB_PASSWORD
MARIADB_CREDENTIALS_FILE=$SCRIPTS_DIR/mariadb_credentials.txt
source $MARIADB_CREDENTIALS_FILE

echo "Populating CoNekT Microbiome with taxonomy data"
$SCRIPTS_DIR/add/add_taxonomy.py --db_admin $DB_ADMIN\
    --db_name $DB_NAME\
    --db_password $DB_PASSWORD\
    --silva_taxonomy_file $DATA_DIR/taxonomy/silva/tax_slv_lsu_138.1.txt\
    --silva_release 138.1\
    --gg_taxonomy_file $DATA_DIR/taxonomy/gg_13_5/gg_13_5_taxonomy.txt\
    --gg_release 13.5\
    --gtdb_taxonomy_file $DATA_DIR/taxonomy/gtdb/bac120_taxonomy_r214.tsv\
    --gtdb_release 214

echo "Populating CoNekT Microbiome with functional data"
$SCRIPTS_DIR/add/add_functional_data.py --db_admin $DB_ADMIN\
    --db_name $DB_NAME\
    --db_password $DB_PASSWORD\
    --interpro_xml $DATA_DIR/functional_data/interpro.xml\
    --gene_ontology_obo $DATA_DIR/functional_data/go.obo\
    --cazyme $DATA_DIR/functional_data/CAZyDB.07302020.fam-activities.txt

echo "Populating CoNekT Microbiome with ontology data"
$SCRIPTS_DIR/add/add_ontologies.py --db_admin $DB_ADMIN\
    --db_name $DB_NAME\
    --db_password $DB_PASSWORD\
    --plant_ontology $DATA_DIR/ontology/plant-ontology.txt\
    --plant_e_c_ontology $DATA_DIR/ontology/peco.tsv\
    --envo $DATA_DIR/ontology/envo_09012024.txt

echo "Populating CoNekT Microbiome with species data"
$SCRIPTS_DIR/add/add_species.py --db_admin $DB_ADMIN\
    --db_name $DB_NAME\
    --db_password $DB_PASSWORD\
    --input_table $DATA_DIR/info_species.tsv

echo "Populating CoNekT Microbiome with gene descriptions"
$SCRIPTS_DIR/add/add_gene_descriptions.py --db_admin $DB_ADMIN\
    --db_name $DB_NAME\
    --db_password $DB_PASSWORD\
    --species_code Zma\
    --gene_descriptions $DATA_DIR/datasets/maize/Zma_cds_descriptions.txt

echo "Populating CoNekT Microbiome with GO annotation"
$SCRIPTS_DIR/add/add_go.py --db_admin $DB_ADMIN\
    --db_name $DB_NAME\
    --db_password $DB_PASSWORD\
    --species_code Zma\
    --go_tsv $DATA_DIR/datasets/maize/Zma_gos.tsv\
    --annotation_source "GOs from InterProScan"

echo "Populating CoNekT Microbiome with InterProScan data"
$SCRIPTS_DIR/add/add_interproscan.py --db_admin $DB_ADMIN\
    --db_name $DB_NAME\
    --db_password $DB_PASSWORD\
    --interproscan_tsv $DATA_DIR/datasets/maize/Zma_interproscan.tsv\
    --species_code Zma

echo "Populating CoNekT Microbiome with samples"
$SCRIPTS_DIR/add/add_samples.py --db_admin $DB_ADMIN\
    --db_name $DB_NAME\
    --db_password $DB_PASSWORD\
    --species_code Zma\
    --sample_annotation $DATA_DIR/datasets/maize/Zma_sample_annotation.txt

echo "Creating a Study for a species and Populating CoNekT Microbiome"
$SCRIPTS_DIR/build/create_study.py --db_admin $DB_ADMIN\
    --db_name $DB_NAME\
    --db_password $DB_PASSWORD\
    --species_code Zma\
    --study_name "Integration of Maize Microbiome and Transcriptome in leaves"\
    --study_description "Integration of Maize Microbiome and Transcriptome in leaves to understand the role of microbiome in plant transcriptome"\
    --study_type expression_metataxonomics\
    --krona_file $DATA_DIR/datasets/maize/Zma_krona.html

 # Populate CoNekT Microbiome with OTUs
 $SCRIPTS_DIR/add/add_otus.py --db_admin $DB_ADMIN\
    --db_name $DB_NAME\
    --db_password $DB_PASSWORD\
    --literature_doi "10.1094/PBIOMES-02-18-0008-R"\
    --amplicon_marker 16S\
    --primer_pair "515F-1401R"\
    --method_description "Brief description of the method used to generate OTUs"\
    --clustering_method open_reference\
    --clustering_algorithm qiime1\
    --clustering_threshold 0.97\
    --clustering_reference_db greengenes\
    --clustering_reference_db_release 13_5\
     --fasta_file $DATA_DIR/datasets/maize/rep_set_conekt.fna

 # Populate CoNekT Microbiome with OTU classification

 
