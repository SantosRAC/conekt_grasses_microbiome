from curses import flash
from flask import redirect, request, url_for
from flask_admin import expose

from conekt.controllers.admin.views import  AdminBaseView
from conekt.forms.admin.add_taxonomy import AddTaxonomyForm


class AddTaxonomyView(AdminBaseView):
    """
    Admin page to add new taxonomy to the database
    """
    @expose('/')
    def index(self):
        form = AddTaxonomyForm()

        return self.render('admin/add/taxonomy.html', form=form)
    
    @expose('/submit', methods=['POST'])
    def submit(self):
        form = AddTaxonomyForm(request.form)
        if form.validate_on_submit():
            try:
                # Processar o arquivo de genomas
                # Aqui você pode adicionar a lógica para salvar o arquivo no servidor
                flash('Taxonomy added!', 'success')
                return redirect(url_for('admin.index'))
            except Exception as e:
                flash(f'Ocorreu um erro ao adicionar os genomas: {e}', 'error')
        else:
            flash('Falha na validação do formulário. Por favor, verifique os dados e tente novamente.', 'error')

        return self.render('admin/add/taxonomy.html', form=form)