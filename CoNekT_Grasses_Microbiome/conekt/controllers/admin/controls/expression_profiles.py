import os
from tempfile import mkstemp

from flask import request, flash, url_for, get_flashed_messages
from conekt.extensions import admin_required
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from conekt.controllers.admin.controls import admin_controls
from conekt.forms.admin.add_expression_profiles import AddExpressionProfilesForm
from conekt.models.expression.profiles import ExpressionProfile
from conekt.models.seq_run import SeqRun


@admin_controls.route('/add/expression_profile', methods=['POST'])
@admin_required
def add_expression_profiles():
    """
    Add expression profiles to sequences based on data from LSTrAP

    :return: Redirect to admin panel interface
    """
    form = AddExpressionProfilesForm(request.form)

    if request.method == 'POST':
        species_id = int(request.form.get('species_id'))

        normalization_method = request.form.get('normalization_method')

        matrix_file = request.files[form.matrix_file.name].read()
        annotation_file = request.files[form.annotation_file.name].read()

        if matrix_file != b'' and annotation_file != b'':
            fd_matrix, temp_matrix_path = mkstemp()

            with open(temp_matrix_path, 'wb') as matrix_writer:
                matrix_writer.write(matrix_file)

            #Add ConditionDescription, PO, and PECO (optional) annotation file
            fd_annotation, temp_annotation_path = mkstemp()
            with open(temp_annotation_path, 'wb') as annotation_writer:
                annotation_writer.write(annotation_file)

            added_runs_count = SeqRun.add_run_annotation(temp_annotation_path,
                                  species_id,
                                  'rnaseq')

            ExpressionProfile.add_profile_from_lstrap(temp_matrix_path, temp_annotation_path,
                                                          species_id)

            os.close(fd_annotation)
            os.remove(temp_annotation_path)
            os.close(fd_matrix)
            os.remove(temp_matrix_path)

            flash('Added expression profiles for species %d' % species_id, 'success')
            flash('Added %d runs' % added_runs_count, 'success')
        else:
            flash('Empty file or no file provided, cannot add expression profiles for species', 'warning')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)