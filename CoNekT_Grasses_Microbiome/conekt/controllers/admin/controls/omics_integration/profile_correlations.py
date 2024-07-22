import os
from tempfile import mkstemp

from flask import request, redirect, url_for, flash, abort
from conekt.extensions import admin_required

from conekt.controllers.admin.controls import admin_controls

from conekt.forms.admin.build_expression_microbiome_correlations import BuildExpMicrobiomeCorrelationsForm
from conekt.models.expression_microbiome.expression_microbiome_correlation import ExpMicroCorrelation

@admin_controls.route('/build/profile_correlations', methods=['POST'])
@admin_required
def build_profile_correlations():
    """
    Controller that will start building correlations for a pair of profiles using Pearson correlation

    :return: return to admin index
    """

    form = BuildExpMicrobiomeCorrelationsForm(request.form)

    if request.method == 'POST' and form.validate():
        study_id = int(request.form.get('study_id'))
        description = request.form.get('description')
        tool = request.form.get('tool')
        stat_method = request.form.get('stat_method')
        multiple_test_cor_method = request.form.get('multiple_test_cor_method')
        rnaseq_norm = request.form.get('rnaseq_norm')
        metatax_norm = request.form.get('metatax_norm')
        correlation_cutoff = float(request.form.get('correlation_cutoff'))
        corrected_pvalue_cutoff = float(request.form.get('corrected_pvalue_cutoff'))

        ExpMicroCorrelation.calculate_expression_metataxonomic_correlations(study_id, description, tool, stat_method,
                                                                    multiple_test_cor_method, rnaseq_norm,
                                                                    metatax_norm)

        flash('Succesfully build correlations between microbiome and transcriptome.', 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)





