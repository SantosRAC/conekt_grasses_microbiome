import json
import contextlib

from conekt import db
from flask import Blueprint, redirect, request, render_template, flash

from conekt import cache
from conekt.forms.microbiome.profile import ProfileComparisonForm

from conekt.helpers.chartjs import prepare_asv_profiles

from conekt.models.microbiome.asvs import AmpliconSequenceVariant
from conekt.models.microbiome.asv_profiles import ASVProfile
from conekt.models.species import Species
from conekt.models.relationships_microbiome.asv_profile_run import ASVProfileRunAssociation
from conekt.models.relationships.study_run import StudyRunAssociation

asvs_profile = Blueprint('asvs_profile', __name__)


@asvs_profile.route('/profile_comparison', methods=['GET', 'POST'])
def asvs_profile_compare():
    """
    TODO: add documentation
    """

    form = ProfileComparisonForm(request.form)
    form.populate_species()

    if request.method == 'POST':
        species_id = request.form.get('species_id')
        study_id = request.form.get('study_id')
        terms = request.form.get('probes').split()

        asvs = AmpliconSequenceVariant.query.with_entities(AmpliconSequenceVariant.id, AmpliconSequenceVariant.original_id).filter(AmpliconSequenceVariant.original_id.in_(terms)).all()

        study_run_ids = [study_run.run_id for study_run in StudyRunAssociation.query.with_entities(StudyRunAssociation.run_id).filter(StudyRunAssociation.study_id == study_id).distinct().all()]

        asv_profiles_ids = [asv_p.asv_profile_id for asv_p in ASVProfileRunAssociation.query.with_entities(ASVProfileRunAssociation.asv_profile_id).filter(ASVProfileRunAssociation.run_id.in_(study_run_ids)).distinct().all()]

        asvs_ids = [asv.id for asv in asvs]
        asvs_original_ids = [asv.original_id for asv in asvs]

        # get max 51 profiles, only show the first 50 (the extra one is fetched to throw the warning)
        asvs_profiles = ASVProfile.get_profiles(asvs_ids, asv_profiles_ids, limit=51)

        not_found = [p.lower() for p in asvs_original_ids]
        for p in asvs_profiles:
            #TODO: revise, maybe include original id in the ASV profile
            with contextlib.suppress(ValueError):
                not_found.remove(p.asv.original_id.lower())

        if len(not_found) > 0:
            flash("Couldn't find profile for: %s" % ", ".join(not_found), "warning")

        if len(asvs_profiles) > 50:
            flash(Markup(("To many profiles in this cluster only showing the <strong>first 50</strong>. <br />" +
                          "<strong>Note:</strong> The <a href='%s'>heatmap</a> can be used to with more genes and " +
                          "allows downloading the data for local analysis.") % url_for('heatmap.heatmap_main')),
                  'warning')

        # Get json object for chart
        profile_chart = prepare_asv_profiles(asvs_profiles[:50], ylabel='Count')

        # Get table in base64 format for download
        #data = base64.encodebytes(prepare_profiles_download(profiles[:50], normalize).encode('utf-8'))

        return render_template("microbiome/asvs_profile_comparison.html",
                               asvs_profiles=json.dumps(profile_chart), form=form)#, data=data.decode('utf-8'))
    else:
        asvs_profiles = ASVProfile.query.filter(ASVProfile.asv_id is not None).limit(5).all()

        example = {
            'probes': None
        }

        if len(asvs_profiles) > 0:
            example['probes'] = ' '.join([p.asv.original_id for p in asvs_profiles])

        return render_template("microbiome/asvs_profile_comparison.html", form=form, example=example)