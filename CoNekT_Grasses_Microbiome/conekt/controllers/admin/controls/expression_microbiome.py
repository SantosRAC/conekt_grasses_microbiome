from flask import request
from conekt.extensions import admin_required

from conekt.controllers.admin.controls import admin_controls

from conekt.forms.admin.build_expression_microbiome_correlations import BuildExpMicrobiomeCorrelationsForm

@admin_controls.route('/build/expression_microbiome_correlations', methods=['POST'])
@admin_required
def build_expression_microbiome_correlations():
    """
    Controller that will start building correlations between expression and microbiome data

    :return: return to admin index
    """
    form = BuildExpMicrobiomeCorrelationsForm(request.form)
    form.populate_studies()
    if request.method == 'POST' and form.validate():
        study_id = int(request.form.get('study_id'))
        description = request.form.get('description')
        CoexpressionClusteringMethod.build_hcca_clusters(description, study_id)

        flash('Succesfully build clusters using HCCA.', 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)