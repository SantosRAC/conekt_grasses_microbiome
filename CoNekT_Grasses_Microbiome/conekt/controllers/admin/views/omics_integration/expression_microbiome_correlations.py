from flask import flash
from flask_admin import expose
from markupsafe import Markup

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.build_expression_microbiome_correlations import BuildExpMicrobiomeCorrelationsForm
from conekt.forms.admin.add_expression_microbiome_correlations import AddExpMicrobiomeCorrelationsForm


class BuildCorrelationsView(AdminBaseView):
    """
    Admin page to compute correlations (Metataxonomics vs. Expression) of a study to the database
    """

    @expose('/')
    def index(self):
        form = BuildExpMicrobiomeCorrelationsForm()
        form.populate_species()

        flash('Please use the script in the current version of CoNekT Grasses Microbiome.', 'danger')
        return self.render('admin/build/profile_correlations.html', form=form)

class AddCorrelationsView(AdminBaseView):

    @expose('/')
    def index(self):
        form = AddExpMicrobiomeCorrelationsForm()
        form.populate_species()

        return self.render('admin/add/profile_correlations.html', form=form)