import json
import contextlib

from conekt import db
from flask import Blueprint, redirect, request, render_template, flash

from conekt import cache

from conekt.forms.microbiome.profile import ProfileComparisonForm
from conekt.forms.microbiome.search_specific_profiles import SearchSpecificProfilesForm

from conekt.helpers.chartjs import prepare_otu_profiles

from conekt.models.microbiome.otu_profiles import OTUProfile
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit

from conekt.models.relationships.study_run import StudyRunAssociation
from conekt.models.relationships_microbiome.otu_profile_run import OTUProfileRunAssociation

from conekt.models.microbiome.specificity import MicrobiomeSpecificityMethod

from conekt.models.studies import Study
from conekt.models.species import Species


otus_profile = Blueprint('otus_profile', __name__)


@otus_profile.route('/view/<profile_id>')
@cache.cached()
def otu_profile_view(profile_id):
    """
    Gets OTU profile data from the database and renders it.

    :param profile_id: ID of the profile to show
    """
    current_profile = OTUProfile.query.get_or_404(profile_id)

    return render_template("otu_profile.html", profile=current_profile)


@otus_profile.route('/profile_comparison', methods=['GET', 'POST'])
def otus_profile_compare():
    """
    TODO: add documentation
    """

    form = ProfileComparisonForm(request.form)
    form.populate_species()

    if request.method == 'POST':
        species_id = request.form.get('species_id')
        study_id = request.form.get('study_id')
        terms = request.form.get('probes').split()

        otus = OperationalTaxonomicUnit.query.with_entities(OperationalTaxonomicUnit.id, OperationalTaxonomicUnit.original_id).filter(OperationalTaxonomicUnit.original_id.in_(terms)).all()

        study_run_ids = [study_run.run_id for study_run in StudyRunAssociation.query.with_entities(StudyRunAssociation.run_id).filter(StudyRunAssociation.study_id == study_id).distinct().all()]

        otu_profiles_ids = [otu_p.otu_profile_id for otu_p in OTUProfileRunAssociation.query.with_entities(OTUProfileRunAssociation.otu_profile_id).filter(OTUProfileRunAssociation.run_id.in_(study_run_ids)).distinct().all()]

        otus_ids = [otu.id for otu in otus]
        otus_original_ids = [otu.original_id for otu in otus]

        # get max 51 profiles, only show the first 50 (the extra one is fetched to throw the warning)
        otus_profiles = OTUProfile.get_profiles(otus_ids, otus_original_ids, limit=51)

        not_found = [p.lower() for p in otus_original_ids]
        for p in otus_profiles:
            #TODO: revise, maybe include original id in the OTU profile
            with contextlib.suppress(ValueError):
                not_found.remove(p.otus.original_id.lower())

        if len(not_found) > 0:
            flash("Couldn't find profile for: %s" % ", ".join(not_found), "warning")

        if len(otus_profiles) > 50:
            flash(Markup(("To many profiles in this cluster only showing the <strong>first 50</strong>. <br />" +
                          "<strong>Note:</strong> The <a href='%s'>heatmap</a> can be used to with more genes and " +
                          "allows downloading the data for local analysis.") % url_for('heatmap.heatmap_main')),
                  'warning')

        # Get json object for chart
        profile_chart = prepare_otu_profiles(otus_profiles[:50], ylabel='Count')

        # Get table in base64 format for download
        #data = base64.encodebytes(prepare_profiles_download(profiles[:50], normalize).encode('utf-8'))

        return render_template("microbiome/otus_profile_comparison.html",
                               otus_profiles=json.dumps(profile_chart), form=form)#, data=data.decode('utf-8'))
    else:
        otus_profiles = OTUProfile.query.filter(OTUProfile.otu_id is not None).limit(5).all()

        example = {
            'probes': None
        }

        if len(otus_profiles) > 0:
            example['probes'] = ' '.join([p.otus.original_id for p in otus_profiles])

        return render_template("microbiome/otus_profile_comparison.html", form=form, example=example)


@otus_profile.route('/profile_specificity', methods=['GET', 'POST'])
def find_specific_profiles():
    """
    TODO: add documentation
    """

    form = SearchSpecificProfilesForm(request.form)
    form.populate_form()

    if request.method == 'POST':
        species_id = request.form.get('species_id')
        study_id = request.form.get('study_id')
        method_id = request.form.get('conditions')
        spm_cutoff = request.form.get('spm_cutoff')

        current_method = MicrobiomeSpecificityMethod.query.get(method_id)
        current_species = Species.query.get(species_id)
        current_study = Study.query.get(study_id)

        specific_profiles = MicrobiomeSpecificityMethod.get_method_specificities(method_id, spm_cutoff)

        return render_template("microbiome/otus_profile_specificity.html",
                               specific_profiles=specific_profiles,
                               current_species=current_species,
                               current_method=current_method,
                               current_study=current_study)
    else:
        
        return render_template("microbiome/otus_profile_specificity.html", form=form)