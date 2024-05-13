from flask_admin import expose

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.build_study import BuildStudyForm

class BuildStudyView(AdminBaseView):
    """
    Admin page to build a study for one species to the database
    """
    @expose('/')
    def index(self):
        form = BuildStudyForm()
        form.populate_species()
        form.literature_list.choices = []

        return self.render('admin/build/study.html', form=form)