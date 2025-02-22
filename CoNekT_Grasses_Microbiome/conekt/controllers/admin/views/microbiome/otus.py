from flask_admin import expose

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.add_otus import AddOTUSForm
from conekt.forms.admin.add_otu_profiles import AddOTUProfilesForm
from conekt.forms.admin.add_otu_classification import AddOTUClassificationForm
from conekt.forms.admin.add_otu_associations import AddOTUAssociationsForm


class AddOTUSView(AdminBaseView):
    """
    Admin page to add microbiome OTUs and representative sequences for one species and study to the database
    """
    @expose('/')
    def index(self):
        form = AddOTUSForm()
        form.populate_species()

        return self.render('admin/add/otus.html', form=form)
    
class AddOTUProfilesView(AdminBaseView):
    """
    Admin page to add microbiome OTU profiles for one species and study to the database
    """
    @expose('/')
    def index(self):
        form = AddOTUProfilesForm()
        form.populate_species()

        return self.render('admin/add/otu_profiles.html', form=form)


class AddOTUClassificationView(AdminBaseView):
    """
    Admin page to add microbiome OTU classification for one species and study to the database
    """
    @expose('/')
    def index(self):
        form = AddOTUClassificationForm()
        form.populate_literature()

        return self.render('admin/add/otu_classification.html', form=form)

class AddOTUAssociationsView(AdminBaseView):
    """
    Admin page to add microbiome OTU associations for one species and study to the database
    """
    @expose('/')
    def index(self):
        form = AddOTUAssociationsForm()
        form.populate_species()

        return self.render('admin/add/otu_associations.html', form=form)