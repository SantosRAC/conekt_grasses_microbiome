from flask import flash
from flask_admin import expose
from markupsafe import Markup

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.add_go_interpro import AddFunctionalDataForm
from conekt.forms.admin.add_go_sequences import AddGOForm
from conekt.forms.admin.add_interpro_sequences import AddInterProForm
from conekt.forms.admin.add_cazyme_sequences import AddCAZYmeForm


class GOEnrichmentView(AdminBaseView):
    """
    Control panel for administrators. Contains links to
    """
    @expose('/')
    def index(self):
        message = Markup('<strong>Note: </strong> some operations on this page can take a long time and slow down the '
                         'database. This can effect the user-experience of others negatively.<br />Also avoid running '
                         'multiple updates simultaniously.')
        flash(message, 'danger')

        return self.render('admin/build/go_enrichment.html')


class AddFunctionalDataView(AdminBaseView):
    """
    Admin page to add GO definitions and InterPro descriptions to the database
    """
    @expose('/')
    def index(self):
        form = AddFunctionalDataForm()

        return self.render('admin/add/functional_data.html', form=form)


class AddGOView(AdminBaseView):
    """
    Admin page to add GO terms for one species to the database
    """
    @expose('/')
    def index(self):
        form = AddGOForm()
        form.populate_species()

        return self.render('admin/add/go.html', form=form)


class AddInterProView(AdminBaseView):
    """
    Admin page to add InterPro domains for one species to the database
    """
    @expose('/')
    def index(self):
        form = AddInterProForm()
        form.populate_species()

        return self.render('admin/add/interpro.html', form=form)

class AddCAZYmeView(AdminBaseView):
    """
    Admin page to add GO terms for one species to the database
    """
    @expose('/')
    def index(self):
        form = AddCAZYmeForm()
        form.populate_species()

        return self.render('admin/add/cazyme.html', form=form)