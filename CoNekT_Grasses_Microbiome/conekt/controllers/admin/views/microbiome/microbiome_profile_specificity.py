from flask import flash
from flask_admin import expose
from markupsafe import Markup

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.build_microbiome_profile_specificity import BuildMicrobiomeSpecificityForm

class BuildMicrobiomeSpecificityView(AdminBaseView):
    """
    Admin page to compute specificity of microbes in sample groups of a study to the database
    """

    @expose('/')
    def index(self):
        form = BuildMicrobiomeSpecificityForm()
        form.populate_species()

        return self.render('admin/build/microbiome_profile_specificity.html', form=form)