from flask_admin import expose

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.add_asvs import AddASVSForm
from conekt.forms.admin.add_asv_classification import AddASVClassificationForm
from conekt.forms.admin.add_asv_profiles import AddASVProfilesForm


class AddASVSView(AdminBaseView):
    """
    Admin page to add microbiome ASVs to the database
    """
    @expose('/')
    def index(self):
        form = AddASVSForm()

        return self.render('admin/add/asvs.html', form=form)

class AddASVClassificationView(AdminBaseView):
    """
    Admin page to add microbiome ASV classification to the database
    """
    @expose('/')
    def index(self):
        form = AddASVClassificationForm()
        form.populate_literature()

        return self.render('admin/add/asv_classification.html', form=form)

class AddASVProfilesView(AdminBaseView):
    """
    Admin page to add microbiome ASV profiles to the database
    """
    @expose('/')
    def index(self):
        form = AddASVProfilesForm()

        return self.render('admin/add/asv_profiles.html', form=form)

