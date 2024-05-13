import os
from tempfile import mkstemp

from flask import request, flash, url_for
from conekt.extensions import admin_required
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from conekt.controllers.admin.controls import admin_controls
from conekt.forms.admin.add_samples import AddSamplesForm
from conekt.models.sample import Sample


@admin_controls.route('/add/samples', methods=['POST'])
@admin_required
def add_samples():
    """
    Adds samples to one particular species.

    :return: Redirect to admin panel interface
    """
    form = AddSamplesForm(request.form)

    if request.method == 'POST' and form.validate():

        species_id = int(request.form.get('species_id'))

        samples_file = request.files[form.samples_file.name].read()

        if not samples_file:
            flash('Missing File. Please, upload File with samples before submission.', 'danger')
            return redirect(url_for('admin.add.samples.index'))

        # Add samples
        fd, temp_path = mkstemp()

        with open(temp_path, 'wb') as file_writer:
            file_writer.write(samples_file)

        samples_count = Sample.add_samples_from_file(temp_path, species_id)

        os.close(fd)
        os.remove(temp_path)

        flash('Added %s samples' % (samples_count), 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)