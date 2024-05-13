import os
from tempfile import mkstemp

from flask import request, flash, url_for
from conekt.extensions import admin_required
from conekt.controllers.admin.controls import admin_controls
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from conekt.forms.admin.add_asvs import AddASVSForm
from conekt.models.microbiome.asvs import AmpliconSequenceVariant
from conekt.models.seq_run import SeqRun
from conekt.models.microbiome.asv_profiles import ASVProfile
from conekt.models.relationships_microbiome.asv_classification import ASVClassification

@admin_controls.route('/add/asvs', methods=['POST'])
@admin_required
def add_asvs():
    """
    Add ASVs based on data from a FASTA, a feature table and a classification file

    :return: Redirect to admin panel interface
    """

    form = AddASVSForm(request.form)

    if request.method == 'POST' and form.validate():

        species_id = int(request.form.get('species_id'))
        literature_doi = request.form.get('literature_doi')

        asv_method_description = request.form.get('asv_method_description')
        asv_source_method = request.form.get('asv_source_method')
        amplicon_marker = request.form.get('amplicon_marker')
        primer_pair = request.form.get('asv_source_method')

        fasta_data_asvs = request.files[form.asvs_file.name].read()

        asv_classification_description = request.form.get('asv_classification_description')
        asv_classification_method = request.form.get('asv_classification_method')
        classifier_version = request.form.get('classifier_version')
        ref_db_release = request.form.get('ref_db_release')

        run_annotation = request.files[form.run_annotation_file.name].read()
        feature_table = request.files[form.feature_table_file.name].read()
        asv_classification_file = request.files[form.asv_classification_file.name].read()

        if not fasta_data_asvs or\
              not feature_table or\
              not asv_classification_file or\
              not run_annotation:
            flash('Missing File. Please, upload all files before submission.', 'danger')
            return redirect(url_for('admin.add.asvs.index'))

        # Add ASVs
        fd, temp_path = mkstemp()

        with open(temp_path, 'wb') as fasta_writer:
            fasta_writer.write(fasta_data_asvs)

        added_asvs_count, asv_method_id = AmpliconSequenceVariant.add_asvs_from_fasta(temp_path,
                                                    asv_method_description,
                                                    asv_source_method,
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
        
        added_profiles_count = ASVProfile.add_asv_profiles_from_table(temp_feature_table_path, species_id, asv_method_id)

        os.close(fd_feature_table)
        os.remove(temp_feature_table_path)

        # Add feature table
        fd_classification_file, temp_classification_file_path = mkstemp()

        with open(temp_classification_file_path, 'wb') as asv_classification_file_writer:
            asv_classification_file_writer.write(asv_classification_file)

        ASVClassification.add_asv_classification_from_table(temp_classification_file_path,
                                    asv_classification_description,
                                    asv_classification_method,
                                    classifier_version,
                                    ref_db_release)

        os.close(fd_classification_file)
        os.remove(temp_classification_file_path)

        flash('Added %d ASVs' % (added_asvs_count), 'success')
        flash('Added %d Runs' % (added_runs_count), 'success')
        flash('Added %d ASV profiles' % (added_profiles_count), 'success')

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)

