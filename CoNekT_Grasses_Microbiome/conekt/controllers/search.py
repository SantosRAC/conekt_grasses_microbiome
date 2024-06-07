from flask import Blueprint, request, render_template
from sqlalchemy.orm import joinedload

search = Blueprint('search', __name__)

from conekt.forms.omics_integration.profile_correlations import SearchCorrelatedProfilesForm
from conekt.models.species import Species
from conekt.models.expression_microbiome.expression_microbiome_correlation import\
    ExpMicroCorrelationMethod, ExpMicroCorrelation


@search.route('/correlated/profiles', methods=['GET', 'POST'])
def search_correlated_profiles():
    """
    Controller that shows the search form to find condition/tissue specific expressed genes

    :return: Html response
    """
    form = SearchCorrelatedProfilesForm(request.form)
    form.populate_form()

    if request.method == 'GET':
        return render_template("omics_integration/find_expression_microbiome_correlations.html", form=form)
    else:
        species_id = request.form.get('species_id')
        study_id = request.form.get('study_id')
        method_id = request.form.get('method')
        cutoff = request.form.get('cutoff')

        species = Species.query.get_or_404(species_id)
        exp_micro_cor_method = ExpMicroCorrelationMethod.query.get_or_404(method_id)
        results = ExpMicroCorrelation.query.\
            filter(ExpMicroCorrelation.method_id == method_id).\
            filter(ExpMicroCorrelation.score>=cutoff).\
            options(
                joinedload(ExpMicroCorrelation.profile).undefer("profile")
            )

        return render_template("omics_integration/find_expression_microbiome_correlations.html", results=results, species=species_id, method=method_id)