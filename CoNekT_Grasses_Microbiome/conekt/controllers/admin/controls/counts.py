from flask import flash, url_for
from conekt.extensions import admin_required
from werkzeug.utils import redirect

from conekt.controllers.admin.controls import admin_controls
from conekt.models.gene_families import GeneFamilyMethod
from conekt.models.go import GO
from conekt.models.species import Species


@admin_controls.route('/update/counts')
@admin_required
def update_counts():
    """
    Controller that will update pre-computed counts in the database.

    :return: Redirect to admin panel interface
    """

    try:
        GeneFamilyMethod.update_count()
    except Exception as e:
        print("ERROR:", e)
        flash('An error occurred while re-doing GeneFamilyMethod counts', 'danger')
    else:
        flash('GeneFamilyMethod count updated', 'success')

    try:
        Species.update_counts()
    except Exception as e:
        print("ERROR:", e)
        flash('An error occurred while re-doing Species counts', 'danger')
    else:
        flash('Species count updated', 'success')

    try:
        GO.update_species_counts()
    except Exception as e:
        print("ERROR:", e)
        flash('An error occurred while re-doing GO counts', 'danger')
    else:
        flash('GO count updated', 'success')

    return redirect(url_for('admin.index'))