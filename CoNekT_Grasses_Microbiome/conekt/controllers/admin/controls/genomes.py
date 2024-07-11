import os
from tempfile import mkstemp

from flask import request, flash, url_for
from conekt.extensions import admin_required
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from conekt.controllers.admin.controls import admin_controls
from conekt.forms.admin.add_genomes import AddGenomesForm
from conekt.models.genome import Genome
from conekt.models.genome_envo import GenomeENVO
from conekt.models.genomes_quality import Genomes_quality
from conekt.models.geographic_genomes_information import Geographic
from conekt.models.ncbi_information import NCBI


@admin_controls.route('/add/genomes', methods=['POST'])
@admin_required
def add_genomes():
    """
    Adds genomes to the database.

    :return: Redirect to admin panel interface
    """
    form = AddGenomesForm(request.form)

    if request.method == 'POST' and form.validate():

        genomes_file = request.files[form.genomes_file.name].read()

        if not genomes_file:
            flash('Missing File. Please, upload File with samples before submission.', 'danger')
            return redirect(url_for('admin.add.genomes.index'))

        # Add genomes
        fd, temp_path = mkstemp()

        with open(temp_path, 'wb') as file_writer:
            file_writer.write(genomes_file)

        genomes_count = Genome.add_genomes_from_file(temp_path)

        os.close(fd)
        os.remove(temp_path)

        flash('Added %s genomes' % (genomes_count), 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)