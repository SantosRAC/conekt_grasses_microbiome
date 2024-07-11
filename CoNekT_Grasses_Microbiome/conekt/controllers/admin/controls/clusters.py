import os
from tempfile import mkstemp

from flask import request, flash, url_for
from conekt.extensions import admin_required
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from conekt.controllers.admin.controls import admin_controls
from conekt.forms.admin.add_clusters import AddClustersForm
from conekt.models.cluster import Cluster


@admin_controls.route('/add/clusters', methods=['POST'])
@admin_required
def add_clusters():
    """
    Adds clusters to the database.

    :return: Redirect to admin panel interface
    """
    form = AddClustersForm(request.form)

    if request.method == 'POST' and form.validate():

        clusters_file = request.files[form.clusters_file.name].read()

        if not clusters_file:
            flash('Missing File. Please, upload File with clusters before submission.', 'danger')
            return redirect(url_for('admin.add.clusters.index'))

        # Add clusters
        fd, temp_path = mkstemp()

        with open(temp_path, 'wb') as file_writer:
            file_writer.write(clusters_file)

        cluster_count = Cluster.add_cluster_from_file(temp_path)

        os.close(fd)
        os.remove(temp_path)

        flash('Added %s clusters' % (cluster_count), 'success')
        return redirect(url_for('admin.index'))
    else:
        if not form.validate():
            flash('Unable to validate data, potentially missing fields', 'danger')
            return redirect(url_for('admin.index'))
        else:
            abort(405)