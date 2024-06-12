
from flask import request, flash, url_for, jsonify
from werkzeug.exceptions import abort
from werkzeug.utils import redirect
from conekt.extensions import admin_required

from conekt.controllers.admin.controls import admin_controls

from conekt.forms.admin.build_study import BuildStudyForm

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

        literature_ids = request.form.getlist('literature_list')

        # Add study to database
        literature_count_study, samples_count = Study.build_study(species_id, study_name, study_description,
                                      study_type, literature_ids)
        
        flash(f'Added {study_type} study with {literature_count_study} associated papers', 'success')
        flash(f'Added {samples_count} associated samples', 'success')

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)