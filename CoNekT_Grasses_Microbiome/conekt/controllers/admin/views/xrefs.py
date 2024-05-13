from flask_admin import expose
from flask import current_app, flash

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.add_xrefs import AddXRefsForm, AddXRefsFamiliesForm


class AddXRefsView(AdminBaseView):
    """
    Admin page to add external references to genes
    """
    @expose('/')
    def index(self):
        form = AddXRefsForm()
        form.populate_species()

        # TODO: implement Sorl indexing

        return self.render('admin/add/xrefs.html', form=form)


class AddXRefsFamiliesView(AdminBaseView):
    """
    Admin page to add external references to families
    """
    @expose('/')
    def index(self):
        form = AddXRefsFamiliesForm()
        form.populate_methods()

        # TODO: implement Solr indexing

        return self.render('admin/add/xrefs_families.html', form=form)