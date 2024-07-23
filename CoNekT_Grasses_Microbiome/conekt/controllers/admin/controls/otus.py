import os
from tempfile import mkstemp

from flask import request, flash, url_for
from conekt.extensions import admin_required
from conekt.controllers.admin.controls import admin_controls
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from conekt.forms.admin.add_otus import AddOTUSForm
from conekt.forms.admin.add_otu_classification import AddOTUClassificationForm
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit
from conekt.models.seq_run import SeqRun
from conekt.models.microbiome.otu_profiles import OTUProfile
from conekt.models.relationships_microbiome.otu_classification import\
                    OTUClassificationGG, OTUClassificationGTDB


@admin_controls.route('/add/otus', methods=['POST'])
@admin_required
def add_otus():
    """
    Add OTUs based on data from a FASTA and a OTU table

    :return: Redirect to admin panel interface
    """

    form = AddOTUSForm(request.form)

    if request.method == 'POST' and form.validate():

        species_id = int(request.form.get('species_id'))
        literature_doi = request.form.get('literature_doi')

        otu_method_description = request.form.get('otu_method_description')
        
        clustering_method = request.form.get('clustering_method')
        clustering_algorithm = request.form.get('clustering_algorithm')
        clustering_threshold = request.form.get('clustering_threshold')
        clustering_reference_database = request.form.get('clustering_reference_database')
        clustering_reference_db_release = request.form.get('clustering_reference_db_release')

        amplicon_marker = request.form.get('amplicon_marker')
        primer_pair = request.form.get('primer_pair')

        fasta_data_otus = request.files[form.otus_file.name].read()

        run_annotation = request.files[form.run_annotation_file.name].read()
        feature_table = request.files[form.feature_table_file.name].read()
        normalization_method = request.form.get('normalization_method')

        if not fasta_data_otus or\
              not feature_table or\
              not run_annotation:
            flash('Missing File. Please, upload all files before submission.', 'danger')
            return redirect(url_for('admin.add.otus.index'))

        # Add OTUs
        fd, temp_path = mkstemp()

        with open(temp_path, 'wb') as fasta_writer:
            fasta_writer.write(fasta_data_otus)

        added_otus_count = OperationalTaxonomicUnit.add_otus_from_fasta(temp_path,
                                                    otu_method_description,
                                                    clustering_method,
                                                    clustering_threshold,
                                                    clustering_algorithm,
                                                    clustering_reference_database,
                                                    clustering_reference_db_release,
                                                    amplicon_marker,
                                                    primer_pair, literature_doi)

        os.close(fd)
        os.remove(temp_path)

        # Add runs and their annotation
        fd_run_annot, temp_run_annot_path = mkstemp()

        with open(temp_run_annot_path, 'wb') as run_annotation_writer:
            run_annotation_writer.write(run_annotation)

        added_runs_count = SeqRun.add_run_annotation(temp_run_annot_path,
                                  species_id,
                                  'metataxonomics')

        os.close(fd_run_annot)
        os.remove(temp_run_annot_path)

        # Add feature table
        fd_feature_table, temp_feature_table_path = mkstemp()

        with open(temp_feature_table_path, 'wb') as feature_table_writer:
            feature_table_writer.write(feature_table)
        
        added_profiles_count = OTUProfile.add_otu_profiles_from_table(temp_feature_table_path, species_id, normalization_method)

        os.close(fd_feature_table)
        os.remove(temp_feature_table_path)

        flash('Added %d OTUs' % (added_otus_count), 'success')
        flash('Added %d Runs' % (added_runs_count), 'success')
        flash('Added %d OTU profiles' % (added_profiles_count), 'success')

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)


@admin_controls.route('/add/otu_classification', methods=['POST'])
@admin_required
def add_otu_classification():
    """
    Add OTU classification file

    :return: Redirect to admin panel interface
    """

    form = AddOTUClassificationForm(request.form)

    if request.method == 'POST' and form.validate():

        otu_classification_description = request.form.get('otu_classification_description')
        otu_classification_method = request.form.get('otu_classification_method_gtdb')
        classifier_version = request.form.get('classifier_version_gtdb')
        classification_ref_db_release = request.form.get('release_gtdb')
        otu_gtdb_classification_file = request.files[form.gtdb_otu_classification_file.name].read()

        exact_path_match_str = request.form.get('exact_path_match')

        if exact_path_match_str == 'True':
            exact_path_match = True
        else:
            exact_path_match = False

        # Add GTDB classification file for OTUs
        fd_gtdb_classification_file, temp_gtdb_classification_file_path = mkstemp()

        with open(temp_gtdb_classification_file_path, 'wb') as otu_gtdb_classification_file_writer:
            otu_gtdb_classification_file_writer.write(otu_gtdb_classification_file)

        OTUClassificationGTDB.add_otu_classification_from_table(temp_gtdb_classification_file_path,
                                    otu_classification_description,
                                    otu_classification_method,
                                    classifier_version,
                                    classification_ref_db_release,
                                    exact_path_match=exact_path_match)

        os.close(fd_gtdb_classification_file)
        os.remove(temp_gtdb_classification_file_path)

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)

