import os
from tempfile import mkstemp

from flask import request
from conekt.extensions import admin_required

from conekt.controllers.admin.controls import admin_controls

from conekt.forms.admin.build_expression_microbiome_correlations import BuildExpMicrobiomeCorrelationsForm

@admin_controls.route('/build/profile_correlations', methods=['POST'])
@admin_required
def build_profile_correlations():
    """
    Controller that will start building correlations for a pair of profiles using Pearson correlation

    :return: return to admin index
    """

    form = BuildExpMicrobiomeCorrelationsForm(request.form)





