#functional_annotation.py
import os
from tempfile import mkstemp

from flask import request, flash, url_for
from conekt.extensions import admin_required
from markupsafe import Markup
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from conekt.controllers.admin.controls import admin_controls
from conekt.forms.admin.add_go_interpro import AddFunctionalDataForm
from conekt.forms.admin.add_go_sequences import AddGOForm
from conekt.forms.admin.add_interpro_sequences import AddInterProForm
from conekt.forms.admin.add_cazyme_sequences import AddCAZYmeForm
from conekt.models.go import GO
from conekt.models.interpro import Interpro
from conekt.models.cazyme import CAZYme


@admin_controls.route('/add/functional_data', methods=['POST'])
@admin_required
def add_functional_data():
    """
    Controller to populate the GO structure and descriptions and InterPro domains with descriptions to the corresponding
    tables.

    Will empty the tables prior to uploading the new information, this might break links with existing GO terms assigned
    to sequences !

    :return: Redirect to admin panel interface
    """
    form = AddFunctionalDataForm(request.form)

    if request.method == 'POST' and form.validate():
        # Add GO
        go_data = request.files[form.go.name].read()
        go_compressed = 'gzip' in request.files[form.go.name].content_type
        if go_data != b'':
            fd, temp_path = mkstemp()

            with open(temp_path, 'wb') as go_writer:
                go_writer.write(go_data)

            GO.add_from_obo(temp_path, empty=True, compressed=go_compressed)

            os.close(fd)
            os.remove(temp_path)
            flash('GO data added.', 'success')
        else:
            flash('No GO data selected, skipping ...', 'warning')

        # Add InterPro
        interpro_data = request.files[form.interpro.name].read()
        if interpro_data != b'':
            fd, temp_path = mkstemp()

            with open(temp_path, 'wb') as interpro_writer:
                interpro_writer.write(interpro_data)

            Interpro.add_from_xml(temp_path, empty=True)

            os.close(fd)
            os.remove(temp_path)
            flash('InterPro data added.', 'success')
        else:
            flash('No InterPro data selected, skipping ...', 'warning')

        # Add CAZYme
        cazyme_data = request.files[form.cazyme.name].read()
        if cazyme_data != b'':
            fd, temp_path = mkstemp()

            with open(temp_path, 'wb') as cazyme_writer:
                cazyme_writer.write(cazyme_data)

            CAZYme.add_from_txt(temp_path, empty=True)

            os.close(fd)
            os.remove(temp_path)
            flash('CAZYme data added.', 'success')
        else:
            flash('No CAZYme data selected, skipping ...', 'warning')

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)


@admin_controls.route('/add/go', methods=['POST'])
@admin_required
def add_go():
    """
    Adds GO labels to sequences using a tab-delimited text-file

    On relation per line like this:

    sequence_name   GO_term evidence_code
    ...

    :return: Redirect to admin panel interface
    """
    form = AddGOForm(request.form)
    form.populate_species()

    if request.method == 'POST':
        species_id = int(request.form.get('species_id'))
        source = request.form.get('source')

        file = request.files[form.file.name].read()
        if file != b'':
            fd, temp_path = mkstemp()

            with open(temp_path, 'wb') as go_writer:
                go_writer.write(file)

            GO.add_go_from_tab(temp_path, species_id, source=source)

            os.close(fd)
            os.remove(temp_path)
            flash('Added GO terms from file %s' % form.file.name, 'success')
        else:
            flash('Empty file or no file provided, cannot add GO terms to sequences', 'warning')

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)


@admin_controls.route('/add/interpro', methods=['POST'])
@admin_required
def add_interpro():
    """
    Adds InterPro domain information to sequences based on InterProScan output

    :return: Redirect to admin panel interface
    """
    form = AddInterProForm(request.form)
    form.populate_species()

    if request.method == 'POST':
        species_id = int(request.form.get('species_id'))

        file = request.files[form.file.name].read()
        if file != b'':
            fd, temp_path = mkstemp()
            with open(temp_path, 'wb') as interpro_writer:
                interpro_writer.write(file)

            Interpro.add_interpro_from_interproscan(temp_path, species_id)

            os.close(fd)
            os.remove(temp_path)
            flash('Added InterPro terms from file %s' % form.file.name, 'success')
        else:
            flash('Empty file or no file provided, cannot add InterPro terms to sequences', 'warning')

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)


@admin_controls.route('/calculate_enrichment')
@admin_required
def calculate_enrichment():
    """
    Controller to start GO enrichment calculations

    :return: Redirect to admin main screen
    """
    try:
        CoexpressionCluster.calculate_enrichment()
    except Exception as e:
        flash(Markup('An error occurred! Please ensure the file is <strong>correctly formatted</strong>' +
                     ' and <strong>update the counts</strong> if necessary'), 'warning')
    finally:
        flash('Successfully calculated GO enrichment for co-expression clusters', 'success')

    return redirect(url_for('controlsview.index'))


@admin_controls.route('/delete_enrichment')
@admin_required
def delete_enrichment():
    """
    Controller to delete all existing GO enrichments

    :return: Redirect to admin main screen
    """
    CoexpressionCluster.delete_enrichment()

    flash('Successfully removed GO enrichment for co-expression clusters', 'success')
    return redirect(url_for('controlsview.index'))


@admin_controls.route('/add/cazyme', methods=['POST'])
@admin_required
def add_cazyme():
    """
    Adds CAZYme labels to sequences using a tab-delimited text-file

    On relation per line like this:

    CAZYme_term sequence_name   evidence_code
    ...

    :return: Redirect to admin panel interface
    """
    form = AddCAZYmeForm(request.form)
    form.populate_species()

    if request.method == 'POST':
        species_id = int(request.form.get('species_id'))

        source = request.form.get('source')

        file = request.files[form.file.name].read()
        if file != b'':
            fd, temp_path = mkstemp()

            with open(temp_path, 'wb') as cazyme_writer:
                cazyme_writer.write(file)

            CAZYme.add_cazyme_from_tab(temp_path, species_id)

            os.close(fd)
            os.remove(temp_path)
            flash('Added CAZYme terms from file %s' % form.file.name, 'success')
        else:
            flash('Empty file or no file provided, cannot add CAZYme terms to sequences', 'warning')

        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)