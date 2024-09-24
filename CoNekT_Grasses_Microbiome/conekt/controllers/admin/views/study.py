from flask_admin import expose

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.build_study import BuildStudyForm
from conekt.forms.admin.build_study_pcas import BuildStudyPCAsForm

class BuildStudyView(AdminBaseView):
    """
    Admin page to build a study for one species in the database
    """
    @expose('/')
    def index(self):
        form = BuildStudyForm()
        form.populate_species()

        return self.render('admin/build/study.html', form=form)


class BuildStudyPCAsView(AdminBaseView):
    """
    Admin page to build PCAs to a particular study for one species in the database
    """
    @expose('/')
    def index(self):
        form = BuildStudyPCAsForm()
        form.populate_species()

        return self.render('admin/build/study_pcas.html', form=form)