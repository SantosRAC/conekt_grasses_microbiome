from flask_admin import expose

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.add_samples import AddSamplesForm

class AddSamplesView(AdminBaseView):
    """
    Admin page to add new samples to the database
    """
    @expose('/')
    def index(self):
        form = AddSamplesForm()
        form.populate_species()

        return self.render('admin/add/samples.html', form=form)