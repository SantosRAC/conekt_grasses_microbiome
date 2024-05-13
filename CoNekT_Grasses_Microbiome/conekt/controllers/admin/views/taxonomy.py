from flask_admin import expose

from conekt.controllers.admin.views import MyModelView, AdminBaseView
from conekt.forms.admin.add_taxonomy import AddTaxonomyForm


class TaxonomyAdminView(MyModelView):
    """
    TODO: Add code and description
    """


class AddTaxonomyView(AdminBaseView):
    """
    Admin page to add new taxonomy to the database
    """
    @expose('/')
    def index(self):
        form = AddTaxonomyForm()

        return self.render('admin/add/taxonomy.html', form=form)