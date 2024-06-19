import os
from tempfile import mkstemp

from flask import request, flash, url_for
from werkzeug.utils import redirect

from conekt.extensions import admin_required
from werkzeug.exceptions import abort

from conekt.controllers.admin.controls import admin_controls
from conekt.forms.admin.add_taxonomy import AddTaxonomyForm
from conekt.models.taxonomy import SILVATaxon, NCBITaxon, GGTaxon, GTDBTaxon

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
        gg_release_info = request.form.get('gg_release')
        gtdb_release_info = request.form.get('gtdb_release')

        ncbi_taxonomy_nodes = request.files[form.ncbi_taxonomy_nodes_file.name].read()
        ncbi_taxonomy_names = request.files[form.ncbi_taxonomy_names_file.name].read()
        silva_taxonomy_data = request.files[form.silva_taxonomy_file.name].read()
        gg_taxonomy_data = request.files[form.gg_taxonomy_file.name].read()
        gtdb_taxonomy_data = request.files[form.gtdb_taxonomy_file.name].read()

        if not ncbi_release_info\
             or not silva_release_info\
             or not gg_release_info\
             or not gtdb_release_info:
            flash('Missing File. Please, add all release information before submission.', 'danger')
            return redirect(url_for('admin.add.taxonomy.index'))

        if not ncbi_taxonomy_nodes\
             or not ncbi_taxonomy_names\
             or not silva_taxonomy_data\
             or not gg_taxonomy_data\
             or not gtdb_taxonomy_data:
            flash('Missing File. Please, upload all taxonomy files before submission.', 'danger')
            return redirect(url_for('admin.add.taxonomy.index'))

        # Add NCBI information
        fd_nodes, temp_path_nodes = mkstemp()
        fd_names, temp_path_names = mkstemp()

        with open(temp_path_nodes, 'wb') as file_writer:
            file_writer.write(ncbi_taxonomy_nodes)
        
        with open(temp_path_names, 'wb') as file_writer:
            file_writer.write(ncbi_taxonomy_names)

        ncbi_taxon_count = NCBITaxon.add_ncbi_taxonomy(temp_path_nodes,
                                                       temp_path_names)

        os.close(fd_nodes)
        os.remove(temp_path_nodes)

        os.close(fd_names)
        os.remove(temp_path_names)

        # Add SILVA information
        fd, temp_path = mkstemp()

        with open(temp_path, 'wb') as file_writer:
            file_writer.write(silva_taxonomy_data)

        silva_taxon_count = SILVATaxon.add_silva_taxonomy(temp_path)

        os.close(fd)
        os.remove(temp_path)

        # Add GG information
        fd, temp_path = mkstemp()

        with open(temp_path, 'wb') as file_writer:
            file_writer.write(gg_taxonomy_data)

        gg_taxon_count = GGTaxon.add_gg_taxonomy(temp_path)

        os.close(fd)
        os.remove(temp_path)

        # Add GTDB information
        fd_gtdb_taxonomy, temp_path_gtdb_taxonomy = mkstemp()
        fd_gtdb_ssu_fasta, temp_path_gtdb_ssu_fasta = mkstemp()

        with open(temp_path, 'wb') as file_writer:
            file_writer.write(gtdb_taxonomy_data)

        gtdb_taxon_count = GTDBTaxon.add_gtdb_taxonomy(temp_path)
        #TODO: Add GTDB SSU fasta file

        os.close(fd_gtdb_taxonomy)
        os.remove(temp_path_gtdb_taxonomy)

        os.close(fd_gtdb_ssu_fasta)
        os.remove(temp_path_gtdb_ssu_fasta)

        flash('Added %s taxon records from SILVA' % (silva_taxon_count), 'success')
        flash('Added %s taxon records from NCBI' % (ncbi_taxon_count), 'success')
        flash('Added %s taxon records from GreenGenes' % (gg_taxon_count), 'success')
        flash('Added %s taxon records from GTDB' % (gtdb_taxon_count), 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)