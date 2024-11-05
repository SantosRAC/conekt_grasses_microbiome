import os
from tempfile import mkstemp

from flask import request, flash, url_for
from conekt.extensions import admin_required
from markupsafe import Markup
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from conekt.controllers.admin.controls import admin_controls
from conekt.forms.admin.add_ontology import AddOntologyDataForm
from conekt.models.ontologies import EnvironmentOntology


@admin_controls.route('/add/ontology', methods=['POST'])
@admin_required
def add_ontology():
    """
    #TODO: Add documentation
    :return: Redirect to admin panel interface
    """
    form = AddOntologyDataForm(request.form)

    if request.method == 'POST' and form.validate():
        envo_data = request.files[form.envo.name].read()

        if envo_data != b'':
            envo_fd, envo_temp_path = mkstemp()

            # Add ENVO
            with open(envo_temp_path, 'wb') as envo_writer:
                envo_writer.write(envo_data)
            
            EnvironmentOntology.add_tabular_envo(envo_temp_path, empty=True)

            os.close(envo_fd)
            os.remove(envo_temp_path)
            flash('Ontologies data added.', 'success')
        else:
            flash('No ontology data selected, skipping ...', 'warning')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)