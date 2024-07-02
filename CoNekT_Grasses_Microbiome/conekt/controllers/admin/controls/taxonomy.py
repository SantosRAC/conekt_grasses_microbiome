import os
from tempfile import mkstemp

from flask import request, flash, url_for
from werkzeug.utils import redirect

from conekt.extensions import admin_required
from werkzeug.exceptions import abort

from conekt.controllers.admin.controls import admin_controls
from conekt.forms.admin.add_taxonomy import AddTaxonomyForm
from conekt.models.taxonomy import GTDBTaxon

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
        
        gtdb_taxonomy_data = request.files[form.gtdb_taxonomy_data.name].read()

        if not gtdb_taxonomy_data:
            flash('missing file. Please upload File with GTDB taxonomy before submission', 'danger')
            return redirect(url_for('admin.add.taxonomy.index'))
        # Add GTDB information

        fd, temp_path = mkstemp()
        

        with open(temp_path, 'wb') as file_writer:
            file_writer.write(gtdb_taxonomy_data)

        taxon_count = GTDBTaxon.add_gtdb_taxonomy(temp_path)
        #TODO: Add GTDB SSU fasta file

        os.close(fd)
        os.remove(temp_path)
      

        flash('Added %s taxon records from GTDB' % (taxon_count), 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)