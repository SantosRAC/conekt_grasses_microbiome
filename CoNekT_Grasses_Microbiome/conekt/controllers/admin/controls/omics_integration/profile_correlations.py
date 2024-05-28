import os
from tempfile import mkstemp

from conekt.extensions import admin_required

from conekt.controllers.admin.controls import admin_controls

@admin_controls.route('/build/hcca_clusters', methods=['POST'])
@admin_required
def build_profile_pearsoncor():
    """
    Controller that will start building correlations for a pair of profiles using Pearson correlation

    :return: return to admin index
    """

