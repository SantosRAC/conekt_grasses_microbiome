import os
from tempfile import mkstemp

from flask import request, flash, url_for
from conekt.extensions import admin_required
from conekt.controllers.admin.controls import admin_controls
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from conekt.forms.admin.add_asvs import AddASVSForm
from conekt.forms.admin.add_asv_classification import AddASVClassificationForm
from conekt.forms.admin.add_asv_profiles import AddASVProfilesForm

from conekt.models.microbiome.asvs import AmpliconSequenceVariant
from conekt.models.seq_run import SeqRun
from conekt.models.microbiome.asv_profiles import ASVProfile
from conekt.models.relationships_microbiome.asv_classification import ASVClassificationSILVA

@admin_controls.route('/add/asvs', methods=['POST'])
@admin_required
def add_asvs():
    """
    Add ASVs based on data from a FASTA, a feature table and a classification file

    :return: Redirect to admin panel interface
    """

    form = AddASVSForm(request.form)

    if request.method == 'POST' and form.validate():

        literature_doi = request.form.get('literature_doi')

        asv_method_description = request.form.get('asv_method_description')
        asv_source_method = request.form.get('asv_source_method')
        amplicon_marker = request.form.get('amplicon_marker')
        primer_pair = request.form.get('primer_pair')

        fasta_data_asvs = request.files[form.asvs_file.name].read()

        if not fasta_data_asvs:
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


        flash('Added %d ASVs' % (added_asvs_count), 'success')

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)


@admin_controls.route('/add/asv_classification', methods=['POST'])
@admin_required
def add_asv_classification():
    """
    Add ASV classification

    :return: Redirect to admin panel interface
    """

    form = AddASVClassificationForm(request.form)

    if request.method == 'POST' and form.validate():

        asv_classification_description = request.form.get('asv_classification_description')
        asv_classification_method = request.form.get('asv_classification_method_silva')
        classifier_version = request.form.get('classifier_version_silva')
        classification_ref_db_release = request.form.get('release_silva')
        asv_silva_classification_file = request.files[form.silva_asv_classification_file.name].read()

        # Add GTDB classification file for ASVs
        fd_silva_classification_file, temp_silva_classification_file_path = mkstemp()

        with open(temp_silva_classification_file_path, 'wb') as asv_silva_classification_file_writer:
            asv_silva_classification_file_writer.write(asv_silva_classification_file)

        ASVClassificationSILVA.add_asv_classification_from_table(temp_silva_classification_file_path,
                                    asv_classification_description,
                                    asv_classification_method,
                                    classifier_version,
                                    classification_ref_db_release)
        
        os.close(fd_silva_classification_file)
        os.remove(temp_silva_classification_file_path)

        flash('Successfully added microbiome classification', 'success')

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)


@admin_controls.route('/add/asv_profiles', methods=['POST'])
@admin_required
def add_asv_profiles():
    """
    Add ASV profiles

    :return: Redirect to admin panel interface
    """

    form = AddASVProfilesForm(request.form)

    if request.method == 'POST' and form.validate():

        

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)

