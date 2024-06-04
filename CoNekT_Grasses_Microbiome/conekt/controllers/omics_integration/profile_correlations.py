from conekt import db

from flask import Blueprint, request

profile_correlations = Blueprint('profile_correlations', __name__)

from conekt.forms.omics_integration.profile_correlations import StudyExprMicrobiomeCorrelationForm

@profile_correlations.route('/exp_metatax_profile_correlations', methods=['GET', 'POST'])
def exp_metatax_profile_correlations():
    """
    TODO: add documentation
    """

    form = StudyExprMicrobiomeCorrelationForm(request.form)
    form.populate_species()

    if request.method == 'POST':
        species_id = request.form.get('species_id')
        study_id = request.form.get('study_id')



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