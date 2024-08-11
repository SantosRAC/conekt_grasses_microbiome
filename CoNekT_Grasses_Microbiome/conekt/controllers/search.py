from flask import Blueprint, request, render_template
from sqlalchemy.orm import joinedload

search = Blueprint('search', __name__)

from conekt.forms.omics_integration.profile_correlations import SearchCorrelatedProfilesGroupsForm,\
    SearchCorrelatedProfilesTwoStudiesForm
from conekt.models.species import Species
from conekt.models.studies import Study
from conekt.models.expression_microbiome.expression_microbiome_correlation import\
    ExpMicroCorrelationMethod, ExpMicroCorrelation


@search.route('/correlated/profiles', methods=['GET', 'POST'])
def search_correlated_profiles():
    """
    Controller that shows the search form to find correlated profiles in a study

    :return: Html response
    """
    form = SearchCorrelatedProfilesGroupsForm(request.form)
    form.populate_form()

    if request.method == 'GET':
        return render_template("omics_integration/find_expression_microbiome_correlations.html",
                               form=form)
    else:
        species_id = request.form.get('species_id')
        study_id = request.form.get('study_id')
        method_id = request.form.get('method_id')
        cutoff = request.form.get('correlation_cutoff_groups')

        species = Species.query.get_or_404(species_id)
        study = Study.query.get_or_404(study_id)
        correlation_method = ExpMicroCorrelationMethod.query.get_or_404(method_id)

        results = ExpMicroCorrelation.query.\
            filter(ExpMicroCorrelation.exp_micro_correlation_method_id == method_id).\
            filter(ExpMicroCorrelation.corr_coef>=cutoff)

        return render_template("omics_integration/find_expression_microbiome_correlations.html",
                               results=results,
                               species=species,
                               study=study,
                               correlation_method=correlation_method)


@search.route('/correlated/profiles_two_studies', methods=['GET', 'POST'])
def search_correlated_profiles_two_studies():
    """
    Controller that shows the search form to find correlations between two studies

    :return: Html response
    """
    form = SearchCorrelatedProfilesTwoStudiesForm(request.form)
    form.populate_form()

    if request.method == 'GET':
        return render_template("omics_integration/compare_correlations_two_studies.html", form=form)
    else:
        species_id = request.form.get('species_id')
        study1_id = request.form.get('study1_id')
        study2_id = request.form.get('study2_id')
        method_id_study2 = request.form.get('method_id')
        cutoff = request.form.get('correlation_cutoff')

        species = Species.query.get_or_404(species_id)
        study1 = Study.query.get_or_404(study1_id)
        study2 = Study.query.get_or_404(study2_id)

        # Get method for study 2 (from filled form) and
        # recover the correlation sets from this method in both studies
        method_study2 = ExpMicroCorrelationMethod.query.get_or_404(method_id_study2)
        method_study1 = ExpMicroCorrelationMethod.query.filter(ExpMicroCorrelationMethod.tool_name == method_study2.tool_name,
                                                               ExpMicroCorrelationMethod.stat_method == method_study2.stat_method,
                                                               ExpMicroCorrelationMethod.rnaseq_norm == method_study2.rnaseq_norm,
                                                               ExpMicroCorrelationMethod.metatax_norm == method_study2.metatax_norm,
                                                               ExpMicroCorrelationMethod.study_id == study1_id).first()

        results_study1 = ExpMicroCorrelation.query.with_entities(ExpMicroCorrelation.gene_probe).\
            filter_by(exp_micro_correlation_method_id=method_study1.id).\
                where(ExpMicroCorrelation.corr_coef>=cutoff).all()
        
        results_study1_list = [x[0] for x in results_study1]
        
        results_study2 = ExpMicroCorrelation.query.with_entities(ExpMicroCorrelation.gene_probe).\
            filter_by(exp_micro_correlation_method_id=method_study2.id).\
                where(ExpMicroCorrelation.corr_coef>=cutoff).all()
        
        results_study2_list = [x[0] for x in results_study2]
        
        results = {'study1': results_study1_list, 'study2': results_study2_list}

        return render_template("omics_integration/compare_correlations_two_studies.html",
                               results=results,
                               species=species,
                               study1=study1,
                               study2=study2,
                               cutoff=cutoff,
                               method_study1=method_study1,
                               method_study2=method_study2)