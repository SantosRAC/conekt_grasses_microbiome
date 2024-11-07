#!/usr/bin/env nextflow

/*
Files needed to store basis of Taxonomy
*/
params.gtdb_file = "$baseDir/data/taxonomy/"
params.silva_file = "$baseDir/data/taxonomy/"
params.gg_file = "$baseDir/data/taxonomy/"
params.ncbi_file = "$baseDir/data/taxonomy/"

/*
Files needed to store basis of Functional Annotation
*/
params.interpro_file = "$baseDir/data/functional_data/interpro.xml"
params.go_file = "$baseDir/data/functional_data/go.obo"
params.cazyme_file = "$baseDir/data/functional_data/cazyme.txt"

/*
Files needed to store basis for the Ontology information
*/
params.po_file = "$baseDir/data/ontology/"
params.peco_file = "$baseDir/data/ontology/"
params.envo_file = "$baseDir/data/ontology/"


/*
 * Add basis for the taxonomy information
 */
process addTaxonomy {

    input:
    path 'input.fa'

    output:
    // Is there any output in this case ?

    script:
    """
    
    """
}

workflow {
    addTaxonomy(params.transcriptome)
}