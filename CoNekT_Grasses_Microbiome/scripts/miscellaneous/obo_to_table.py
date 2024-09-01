#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser(description='Convert the OBO ontology file to a table')
parser.add_argument('-i', '--input_obo', type=str, dest='obo_file', metavar='envo.obo',
                    help='The OBO file to convert', required=True)
parser.add_argument('-o', '--output', type=str, dest='output_file', metavar='output.tsv',
                    help='The output file to write the table to', required=True)
parser.add_argument('--ontology', type=str, dest='ontology_type', metavar='ENVO',
                    choices=['PECO', 'ENVO', 'PO'], help='Ontology (e.g. \'PECO\', \'ENVO\' or \'PO\')', required=True)
args = parser.parse_args()

obo_file = args.obo_file
output_table = args.output_file
ontology = args.ontology_type

output_table_obj = open(output_table, 'w')

output_table_obj.write("id\tname\tdefn\n")

with open(obo_file) as f:

    typedef = 0
    current_term = 0
    printed_to_file = 1
    ontology_id = ''
    ontology_name = ''
    ontology_def = ''

    for line in f:
        # Skip empty
        line = line.rstrip('\n')

        if not line:
            if (not printed_to_file) and ontology_id and ontology_name:
                output_table_obj.write(ontology_id+"\t"+ontology_name+"\tno_ontology_definition\n")
            current_term = 0
            ontology_id = ''
            ontology_name = ''
            ontology_def = ''
            printed_to_file = 0
            typedef = 0
            continue

        if line == "[Term]":

            if current_term:
                print(f'Something wrong. Current term ({current_term}) exists.')
                exit(1)
            current_term = 1
        
        if line == "[Typedef]":

            if current_term or typedef:
                print(f'Something wrong. Current typedef ({typedef}) or a current term ({current_term}) exists.')
                exit(1)
            typedef = 1

        if line.startswith(f'id: {ontology}:'):
            if current_term:
                ontology_id = line.replace('id: ', '')
            else:
                #ontology_id = line.replace('id: ', '')
                #print(f'Something wrong. Found ID ({ontology_id}), but [Term] flag was not recorded.')
                # Here are cases with typedefs as I could note. We are not interested in them.
                continue

        if line.startswith("name: "):
            
            if current_term:
                if ontology_id:
                    ontology_name = line.replace('name: ', '')
                else:
                    continue
                    #ontology_name = line.replace('name: ', '')
                    #print(f'Something wrong. Found Name ({ontology_name}), but no ID was recorded.')
            else:
                #ontology_name = line.replace('name: ', '')
                #print(f'Something wrong. Found Name ({ontology_name}), but [Term] flag was not recorded. ({ontology_id})')
                continue

        if line.startswith("def: "):
        
            if current_term:

                if typedef: # Skip typedefs (relations). We are interested in the nodes in the current implementation
                    continue

                if ontology_id and ontology_name:
                    ontology_def = line.replace('def: ', '')
                    output_table_obj.write(ontology_id+"\t"+ontology_name+"\t"+ontology_def+"\n")
                    printed_to_file = 1
                    ontology_id = ''
                    ontology_name = ''
                    ontology_def = ''
                    current_term = 0
                else:
                    continue
                    #ontology_def = line.replace('def: ', '')
                    #print(f'Something is wrong with Ontology ID. Definition was found ({ontology_def}), but no ID or Name was recorded.')
            
            else:
                #ontology_def = line.replace('def: ', '')
                #print(f'Something wrong. Found Definition ({ontology_def}), but [Term] flag was not recorded.')
                continue

output_table_obj.close()