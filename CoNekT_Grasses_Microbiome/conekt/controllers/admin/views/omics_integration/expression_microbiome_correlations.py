from flask import flash
from flask_admin import expose
from markupsafe import Markup

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.add_expression_microbiome_correlations import AddExpMicrobiomeCorrelationsForm
from conekt.forms.admin.add_expression_microbiome_correlations_go_enrichment import AddExpMicrobiomeCorrelationsGOEnrichForm

class AddCorrelationsView(AdminBaseView):

    @expose('/')
    def index(self):
        form = AddExpMicrobiomeCorrelationsForm()
        form.populate_species()

        return self.render('admin/add/profile_correlations.html', form=form)

class AddGOEnrichCorrelationsView(AdminBaseView):

    @expose('/')
    def index(self):
        form = AddExpMicrobiomeCorrelationsGOEnrichForm()
        form.populate_species()

        return self.render('admin/add/profile_correlations_go_enrichment.html', form=form)