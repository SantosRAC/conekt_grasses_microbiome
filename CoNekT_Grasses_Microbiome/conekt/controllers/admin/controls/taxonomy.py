import os
from tempfile import mkstemp

from flask import request, flash, url_for
from werkzeug.utils import redirect

from conekt.extensions import admin_required
from werkzeug.exceptions import abort

from conekt.controllers.admin.controls import admin_controls
from conekt.forms.admin.add_taxonomy import AddTaxonomyForm
from conekt.models.taxonomy import SILVATaxon

@admin_controls.route('/add/taxonomy', methods=['POST'])
@admin_required
def add_taxonomy():
    """
    Adds taxonomy information.

    Admins can add NCBI Taxonomy and SILVA Taxonomy information to the database.
    :return: Redirect to admin panel interface
    """
    form = AddTaxonomyForm(request.form)

    if request.method == 'POST' and form.validate():
        
        ncbi_release_info = request.form.get('ncbi_release')
        silva_release_info = request.form.get('silva_release')

        ncbi_taxonomy_data = request.files[form.ncbi_taxonomy_file.name].read()
        silva_taxonomy_data = request.files[form.silva_taxonomy_file.name].read()

        if not ncbi_release_info or not silva_release_info:
            flash('Missing File. Please, add release information before submission.', 'danger')
            return redirect(url_for('admin.add.taxonomy.index'))

        if not ncbi_taxonomy_data or not silva_taxonomy_data:
            flash('Missing File. Please, upload both Taxonomy Files before submission.', 'danger')
            return redirect(url_for('admin.add.taxonomy.index'))

        # Add NCBI information
        fd, temp_path = mkstemp()

        with open(temp_path, 'wb') as file_writer:
            file_writer.write(ncbi_taxonomy_data)

        silva_taxon_count = SILVATaxon.add_silva_taxonomy(temp_path)

        os.close(fd)
        os.remove(temp_path)

        flash('Added %s taxon records from SILVA' % (silva_taxon_count), 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)