from flask import flash, redirect, url_for, request
from flask_admin import expose

from conekt.controllers.admin.views import AdminBaseView
from conekt.forms.admin.add_genomes import AddGenomesForm

class AddGenomesView(AdminBaseView):
    """
    Página de administração para adicionar novas amostras ao banco de dados
    """

    @expose('/')
    def index(self):
        form = AddGenomesForm()
        return self.render('admin/add/genomes.html', form=form)

    @expose('/submit', methods=['POST'])
    def submit(self):
        form = AddGenomesForm(request.form)
        if form.validate_on_submit():
            try:
                # Processar o arquivo de genomas
                # Aqui você pode adicionar a lógica para salvar o arquivo no servidor
                flash('Genomas adicionados com sucesso.', 'success')
                return redirect(url_for('admin.index'))
            except Exception as e:
                flash(f'Ocorreu um erro ao adicionar os genomas: {e}', 'error')
        else:
            flash('Falha na validação do formulário. Por favor, verifique os dados e tente novamente.', 'error')

        return self.render('admin/add/genomes.html', form=form)
