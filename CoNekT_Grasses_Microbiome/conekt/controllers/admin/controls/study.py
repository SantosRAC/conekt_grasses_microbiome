
from flask import request, flash, url_for, jsonify
from werkzeug.exceptions import abort
from werkzeug.utils import redirect
from conekt.extensions import admin_required

import os
from tempfile import mkstemp

from conekt.controllers.admin.controls import admin_controls

from conekt.forms.admin.build_study import BuildStudyForm
from conekt.forms.admin.build_study_pcas import BuildStudyPCAsForm

from conekt.models.studies import Study


@admin_controls.route('/build/study', methods=['GET', 'POST'])
@admin_required
def build_study():
    """
    Adds a study to the study table.
    
    If RNAseq and metataxonomic data exists for same samples, indicate their associations. 

    :return: Redirect to admin panel interface
    """
    form = BuildStudyForm(request.form)

    if request.method == 'POST' and form.validate():

        species_id = int(request.form.get('species_id'))
        study_name = request.form.get('study_name')
        study_description = request.form.get('study_description')
        study_type = request.form.get('study_type')

        krona_file = request.files[form.krona_file.name].read()

        # Add Krona plot to study
        fd, temp_path = mkstemp()

        with open(temp_path, 'wb') as file_writer:
            file_writer.write(krona_file)

        # Add study to database
        study_id = Study.build_study(species_id, study_name, study_description,
                                      study_type, krona_file)

        os.close(fd)
        os.remove(temp_path)
        
        flash(f'Added {study_type} study (study identifier: {study_id})', 'success')

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)


@admin_controls.route('/build/study_pcas', methods=['POST'])
@admin_required
def build_study_pcas():
    """
    Controller that will build PCAs using profiles in a study

    :return: return to admin index
    """

    form = BuildStudyPCAsForm(request.form)

    if request.method == 'POST' and form.validate():
        study_id = int(request.form.get('study_id'))
        
        expression_pca_html = request.files[form.expression_pca_file.name].read()
        metatax_pca_html = request.files[form.metatax_pca_file.name].read()

        # Add PCA plots to study
        fd_expression_pca, temp_path_expression_pca = mkstemp()

        with open(temp_path_expression_pca, 'wb') as file_writer:
            file_writer.write(expression_pca_html)

        os.close(fd_expression_pca)
        os.remove(temp_path_expression_pca)

        fd_metatax_pca, temp_path_metatax_pca = mkstemp()

        with open(temp_path_metatax_pca, 'wb') as file_writer:
            file_writer.write(metatax_pca_html)

        os.close(fd_metatax_pca)
        os.remove(temp_path_metatax_pca)

        # Add PCAs to study
        Study.build_pcas_study(study_id, expression_pca_html, metatax_pca_html)

        flash('Successfully added PCAs for the study.', 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)