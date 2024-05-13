from flask_admin import expose

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.add_asvs import AddASVSForm


class AddASVSView(AdminBaseView):
    """
    Admin page to add microbiome profiles for one species and study to the database
    """
    @expose('/')
    def index(self):
        form = AddASVSForm()
        form.populate_species()

        return self.render('admin/add/asvs.html', form=form)