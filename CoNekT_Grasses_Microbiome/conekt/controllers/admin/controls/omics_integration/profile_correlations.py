import os
from tempfile import mkstemp

from flask import request, redirect, url_for, flash, abort
from conekt.extensions import admin_required

from conekt.controllers.admin.controls import admin_controls

from conekt.forms.admin.add_expression_microbiome_correlations import AddExpMicrobiomeCorrelationsForm
from conekt.forms.admin.add_expression_microbiome_correlations_go_enrichment import AddExpMicrobiomeCorrelationsGOEnrichForm
from conekt.models.expression_microbiome.expression_microbiome_correlation import ExpMicroCorrelation
from conekt.models.expression_microbiome.pairs_go_enrichment import GroupCorPairsGOEnrichment


@admin_controls.route('/add/profile_correlations', methods=['POST'])
@admin_required
def add_profile_correlations():
    """
    Controller that will add correlations for profiles in a study

    :return: return to admin index
    """

    form = AddExpMicrobiomeCorrelationsForm(request.form)

    if request.method == 'POST' and form.validate():
        study_id = int(request.form.get('study_id'))
        description = request.form.get('description')
        stat_method = request.form.get('stat_method')
        sample_group = request.form.get('sample_group')
        matrix_file = request.files[form.matrix_file.name].read()

        if matrix_file != b'':
            fd_matrix, temp_matrix_path = mkstemp()

            with open(temp_matrix_path, 'wb') as matrix_writer:
                matrix_writer.write(matrix_file)

            ExpMicroCorrelation.add_expression_metataxonomic_correlations(study_id, description, sample_group,
                                                                          stat_method, temp_matrix_path)

            os.close(fd_matrix)
            os.remove(temp_matrix_path)

        else:
            flash('Empty file or no file provided, cannot add correlations of profiles for species', 'warning')

        flash('Successfully added correlations between microbiome and transcriptome.', 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)



@admin_controls.route('/add/go_enrichment_profile_correlations', methods=['POST'])
@admin_required
def add_go_enrichment_profile_correlations():
    """
    Controller that will add GO enrichment for cross-correlations of profiles in a study

    :return: return to admin index
    """

    form = AddExpMicrobiomeCorrelationsGOEnrichForm(request.form)

    if request.method == 'POST' and form.validate():

        go_enrichment_method = request.form.get('go_enrichment_method')
        exp_microbiome_correlation_method = request.form.get('exp_microbiome_correlation_method')
        go_enrichment_file = request.files[form.go_enrichment_file.name].read()
        correlation_threshold = float(request.form.get('correlation_threshold'))

        if go_enrichment_file != b'':
            fd_go_enrichment_file, temp_go_enrichment_file_path = mkstemp()

            with open(temp_go_enrichment_file_path, 'wb') as go_enrichment_file_writer:
                go_enrichment_file_writer.write(go_enrichment_file)

            GroupCorPairsGOEnrichment.add_go_enrichment_expression_metataxonomic_correlations(exp_microbiome_correlation_method,
                                                                          temp_go_enrichment_file_path, correlation_threshold, go_enrichment_method)

            os.close(fd_go_enrichment_file)
            os.remove(temp_go_enrichment_file_path)

        else:
            flash('Empty file or no file provided, cannot add GO enrichment for correlations of profiles for species', 'warning')

        flash('Successfully added GO enrichement for correlations between microbiome and transcriptome.', 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)
