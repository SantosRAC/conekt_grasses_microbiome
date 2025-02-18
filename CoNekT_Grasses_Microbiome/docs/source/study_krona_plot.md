# Krona Plot

## Creating a Krona text file from the GTDB Taxonomy assignments

Using `gtdb_to_krona.py` and the taxonomy file for a study to create the Krona txt file:

```bash
maize_transcriptome_microbiome_networks/general/gtdb_to_krona.py --input projects/fapesp_bepe_pd/microbiome/gtdb_taxonomy.tsv --output Zma_krona_text.txt
```

Using `ktImportText` to create the HTML file with the krona plot:

```bash
ktImportText -o Zma_krona.html -n Domain Zma_krona_text.txt
```

This HTML must be passed when creating a study in CoNekT Grasses Microbiome.