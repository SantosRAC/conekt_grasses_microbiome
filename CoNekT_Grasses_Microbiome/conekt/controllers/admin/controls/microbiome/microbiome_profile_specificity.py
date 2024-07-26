from flask import request, redirect, url_for, flash, abort
from conekt.extensions import admin_required

from conekt.forms.admin.build_microbiome_profile_specificity import BuildMicrobiomeSpecificityForm

from conekt.models.microbiome.specificity import ExpressionSpecificityMethod

from conekt.controllers.admin.controls import admin_controls

@admin_controls.route('/build/profile_correlations', methods=['POST'])
@admin_required
def build_profile_specificity():
    """
    Controller that will start building correlations for a pair of profiles using Pearson correlation

    :return: return to admin index
    """

    form = BuildMicrobiomeSpecificityForm(request.form)

    if request.method == 'POST' and form.validate():

        study_id = int(request.form.get('study_id'))

        ExpressionSpecificityMethod.calculate_specificities(study_id)

        flash('Succesfully build specificity for microbiome in this study.', 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)