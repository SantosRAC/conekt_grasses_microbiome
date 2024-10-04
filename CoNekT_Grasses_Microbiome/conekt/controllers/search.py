from flask import Blueprint, request, render_template
from sqlalchemy.orm import joinedload

search = Blueprint('search', __name__)

from conekt.forms.omics_integration.profile_correlations import SearchCorrelatedProfilesGroupForm,\
    SearchCorrelatedProfilesTwoStudiesForm, SearchCorrelatedProfilesStudyGroupsForm
from conekt.models.species import Species
from conekt.models.studies import Study
from conekt.models.relationships.study_sample import StudySampleAssociation
from conekt.models.relationships.sample_group import SampleGroupAssociation
from conekt.models.expression_microbiome.expression_microbiome_correlation import\
    ExpMicroCorrelationMethod, ExpMicroCorrelation


@search.route('/correlated/profiles', methods=['GET', 'POST'])
def search_correlated_profiles():
    """
    Controller that shows the search form to find correlated profiles in a study

    :return: Html response
    """
    form = SearchCorrelatedProfilesGroupForm(request.form)
    form.populate_form()

    if request.method == 'GET':
        return render_template("omics_integration/find_expression_microbiome_correlations.html",
                               form=form)
    else:
        species_id = request.form.get('species_id')
        study_id = request.form.get('study_id')
        method_id = request.form.get('method_id')
        sample_group = request.form.get('sample_group')
        cutoff = request.form.get('correlation_cutoff_groups')

        species = Species.query.get_or_404(species_id)
        study = Study.query.get_or_404(study_id)
        correlation_method = ExpMicroCorrelationMethod.query.get_or_404(method_id)

        results = ExpMicroCorrelation.query.\
            filter(ExpMicroCorrelation.exp_micro_correlation_method_id == method_id).\
            filter((ExpMicroCorrelation.corr_coef>=float(cutoff)) | (ExpMicroCorrelation.corr_coef<=-float(cutoff)))

        return render_template("omics_integration/find_expression_microbiome_correlations.html",
                               results=results,
                               species=species,
                               study=study,
                               sample_group=sample_group,
                               correlation_method=correlation_method)


@search.route('/correlated/profiles_study_groups', methods=['GET', 'POST'])
def search_correlated_profiles_study_groups():
    """
    Controller that shows the search form to find correlations between two studies

    :return: Html response
    """
    form = SearchCorrelatedProfilesStudyGroupsForm(request.form)
    form.populate_form()

    if request.method == 'GET':
        return render_template("omics_integration/compare_correlations_study_groups.html", form=form)
    else:
        species_id = request.form.get('species_id')
        study_id = request.form.get('study_id')
        tool_name = request.form.get('tool_name')
        cutoff = request.form.get('correlation_cutoff_study_groups')

        species = Species.query.get_or_404(species_id)
        study = Study.query.get_or_404(study_id)

        sample_ids = [sample_id[0] for sample_id in StudySampleAssociation.query.\
            with_entities(StudySampleAssociation.sample_id).\
            filter_by(study_id=study_id).distinct().all()]
        
        sample_group_associations = SampleGroupAssociation.query.filter(SampleGroupAssociation.sample_id.in_(sample_ids)).all()

        group_type2name = {}

        for sample_group in sample_group_associations:
            if sample_group.group_name not in group_type2name.keys():
                group_type2name[sample_group.group_name] = sample_group.group_type

        results_methods = ExpMicroCorrelationMethod.query.\
            filter_by(study_id=study_id,
                      tool_name=tool_name).all()

        results_correlations = {}

        for method in results_methods:
            # Get all correlations passing the cutoff for the method

            correlation_results = ExpMicroCorrelation.query.\
                filter(ExpMicroCorrelation.exp_micro_correlation_method_id == method.id).\
                where((ExpMicroCorrelation.corr_coef>=float(cutoff)) | (ExpMicroCorrelation.corr_coef<=-float(cutoff))).all()

            results_correlations[method.sample_group] = {}
            if method.sample_group in group_type2name.keys():
                results_correlations[method.sample_group]['group_type'] = group_type2name[method.sample_group]
            else:
                results_correlations[method.sample_group]['group_type'] = 'whole study'
            results_correlations[method.sample_group]['neg'] = {}
            results_correlations[method.sample_group]['pos'] = {}
            results_correlations[method.sample_group]['neg']['pairs'] = []
            results_correlations[method.sample_group]['pos']['pairs'] = []

            for corr in correlation_results:
                if float(corr.corr_coef) >= 0:
                    results_correlations[method.sample_group]['pos'][corr.id] = {}
                    results_correlations[method.sample_group]['pos'][corr.id]['corr_coef'] = corr.corr_coef
                    results_correlations[method.sample_group]['pos'][corr.id]['gene_probe'] = corr.gene_probe
                    results_correlations[method.sample_group]['pos'][corr.id]['otu_probe'] = corr.otu_probe
                    results_correlations[method.sample_group]['pos']['pairs'].append((corr.gene_probe, corr.otu_probe))
                else:
                    results_correlations[method.sample_group]['neg'][corr.id] = {}
                    results_correlations[method.sample_group]['neg'][corr.id]['corr_coef'] = corr.corr_coef
                    results_correlations[method.sample_group]['neg'][corr.id]['gene_probe'] = corr.gene_probe
                    results_correlations[method.sample_group]['neg'][corr.id]['otu_probe'] = corr.otu_probe
                    results_correlations[method.sample_group]['neg']['pairs'].append((corr.gene_probe, corr.otu_probe))

        all_pairs_pos = [results_correlations[sample_group]['pos']['pairs'] for sample_group in results_correlations.keys()]
        all_pairs_neg = [results_correlations[sample_group]['neg']['pairs'] for sample_group in results_correlations.keys()]

        # Convert the lists to sets
        sets_pos = [set(lst) for lst in all_pairs_pos]
        sets_neg = [set(lst) for lst in all_pairs_neg]

        # Get the union of all the sets of positive and negative correlation pairs
        union_pos = set.union(*sets_pos)
        union_neg = set.union(*sets_neg)

        print("union pos: ", union_pos)
        print("union neg: ", union_neg)

        unique_pairs_pos = {}
        unique_pairs_neg = {}
        intersection_two_groups_pos = {}
        intersection_two_groups_neg = {}
        intersection_two_groups_pos_neg = {}
        intersection_two_groups_neg_pos = {}

        for sample_group1 in results_correlations.keys():
            pairs_all_other_groups_pos = []
            pairs_all_other_groups_neg = []
            intersection_two_groups_pos[sample_group1] = {}
            intersection_two_groups_neg[sample_group1] = {}
            intersection_two_groups_pos_neg[sample_group1] = {}
            intersection_two_groups_neg_pos[sample_group1] = {}
            for sample_group2 in results_correlations.keys():
                if sample_group1 != sample_group2:
                    pairs_all_other_groups_pos.extend(results_correlations[sample_group2]['pos']['pairs'])
                    pairs_all_other_groups_neg.extend(results_correlations[sample_group2]['neg']['pairs'])
            for sample_group2 in results_correlations.keys():
                if sample_group2 in intersection_two_groups_pos.keys():
                    if sample_group1 in intersection_two_groups_pos[sample_group2].keys():
                        continue
                if sample_group1 != sample_group2:
                    intersection_two_groups_pos[sample_group1][sample_group2] = set(results_correlations[sample_group1]['pos']['pairs']).intersection(set(results_correlations[sample_group2]['pos']['pairs']))
                    intersection_two_groups_neg[sample_group1][sample_group2] = set(results_correlations[sample_group1]['neg']['pairs']).intersection(set(results_correlations[sample_group2]['neg']['pairs']))
                    intersection_two_groups_pos_neg[sample_group1][sample_group2] = set(results_correlations[sample_group1]['pos']['pairs']).intersection(set(results_correlations[sample_group2]['neg']['pairs']))
                    intersection_two_groups_neg_pos[sample_group1][sample_group2] = set(results_correlations[sample_group1]['neg']['pairs']).intersection(set(results_correlations[sample_group2]['pos']['pairs']))
            unique_pairs_pos[sample_group1] = set(results_correlations[sample_group1]['pos']['pairs']).difference(set(pairs_all_other_groups_pos))
            unique_pairs_neg[sample_group1] = set(results_correlations[sample_group1]['neg']['pairs']).difference(set(pairs_all_other_groups_neg))

        return render_template("omics_integration/compare_correlations_study_groups.html",
                               results=results_correlations,
                               union_pos=union_pos,
                               union_neg=union_neg,
                               intersection_two_groups_pos=intersection_two_groups_pos,
                               intersection_two_groups_neg=intersection_two_groups_neg,
                               intersection_two_groups_pos_neg=intersection_two_groups_pos_neg,
                               intersection_two_groups_neg_pos=intersection_two_groups_neg_pos,
                               unique_pairs_pos=unique_pairs_pos,
                               unique_pairs_neg=unique_pairs_neg,
                               species=species,
                               study=study,
                               tool_name=tool_name,
                               cutoff=cutoff)


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