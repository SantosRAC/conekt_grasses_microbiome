from flask_admin import expose

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.add_otus import AddOTUSForm


class AddOTUSView(AdminBaseView):
    """
    Admin page to add microbiome OTU profiles for one species and study to the database
    """
    @expose('/')
    def index(self):
        form = AddOTUSForm()
        form.populate_species()

        return self.render('admin/add/otus.html', form=form)