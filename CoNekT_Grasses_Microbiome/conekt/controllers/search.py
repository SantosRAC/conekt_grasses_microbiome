from flask import Blueprint, request, render_template
from sqlalchemy.orm import joinedload

search = Blueprint('search', __name__)

from conekt.forms.omics_integration.profile_correlations import SearchCorrelatedProfilesForm


@search.route('/correlated/profiles', methods=['GET', 'POST'])
def search_correlated_profiles():
    """
    Controller that shows the search form to find condition/tissue specific expressed genes

    :return: Html response
    """
    form = SearchCorrelatedProfilesForm(request.form)
    form.populate_form()

    #if request.method == 'POST':
    #    species_id = request.form.get('species_id')
    #    study_id = request.form.get('study_id')

    if request.method == 'GET':
        return render_template("omics_integration/find_expression_microbiome_correlations.html", form=form)
    else:
        species_id = request.form.get('species')
        method_id = request.form.get('methods')
        condition = request.form.get('conditions')
        cutoff = request.form.get('cutoff')

        species = Species.query.get_or_404(species_id)
        method = ExpressionSpecificityMethod.query.get_or_404(method_id)
        results = ExpressionSpecificity.query.\
            filter(ExpressionSpecificity.method_id == method_id).\
            filter(ExpressionSpecificity.score>=cutoff).\
            filter(ExpressionSpecificity.condition == condition).\
            options(
                joinedload(ExpressionSpecificity.profile).undefer("profile")
            )

        return render_template("omics_integration/find_expression_microbiome_correlations.html", results=results, species=species, method=method, condition=condition)