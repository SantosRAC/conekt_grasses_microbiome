#!/usr/bin/env python3

import argparse


# Create arguments
parser = argparse.ArgumentParser(description='Add gene families to the database')
parser.add_argument('--orthogroups', type=str, metavar='Orthogroups.txt',
                    dest='orthogroups_file',
                    help='The Orthogroups.txt file from OrthoFinder',
                    required=True)
parser.add_argument('--description', type=str, metavar='Description',
                    dest='description',
                    help='Description of the method as it should appear in CoNekT',
                    required=True)
parser.add_argument('--db_admin', type=str, metavar='DB admin',
                    dest='db_admin',
                    help='The database admin user',
                    required=True)
parser.add_argument('--db_name', type=str, metavar='DB name',
                    dest='db_name',
                    help='The database name',
                    required=True)
parser.add_argument('--db_password', type=str, metavar='DB password',
                    dest='db_password',
                    help='The database password',
                    required=False)

args = parser.parse_args()

if args.db_password:
    db_password = args.db_password
else:
    db_password = input("Enter the database password: ")