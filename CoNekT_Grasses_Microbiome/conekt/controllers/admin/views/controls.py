from flask import flash
from flask_admin import expose

from conekt.controllers.admin.views import AdminBaseView
from conekt.models.gene_families import GeneFamilyMethod


class ControlsView(AdminBaseView):
    """
    Control panel for administrators. Contains links to endpoints that will start counts, updates, clear cache, ...
    """
    @expose('/')
    def index(self):
        flash('Note: some operations on this page can take a long time and slow down the '+
                         'database. This can effect the user-experience of others negatively. Also avoid running '+
                         'multiple updates simultaniously.', 'danger')

        gene_family_methods = GeneFamilyMethod.query.all()

        return self.render('admin/controls.html', gene_family_methods=gene_family_methods)
