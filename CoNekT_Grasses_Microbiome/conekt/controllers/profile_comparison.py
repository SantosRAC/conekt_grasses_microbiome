import json
import base64
import contextlib

from conekt import db
from flask import Blueprint, request, render_template, flash, url_for, jsonify
from sqlalchemy.orm import noload

from conekt import cache
from conekt.forms.profile_comparison import ProfileComparisonForm
from conekt.helpers.chartjs import prepare_profiles, prepare_profiles_download
from conekt.models.expression.profiles import ExpressionProfile
from conekt.models.sequences import Sequence
from conekt.models.species import Species
from conekt.models.ontologies import PlantOntology
from conekt.models.relationships.sample_literature import SampleLitAssociation
from conekt.models.literature import LiteratureItem

profile_comparison = Blueprint('profile_comparison', __name__)


@profile_comparison.route('/', methods=['GET', 'POST'])
def profile_comparison_main():
    """
    Profile comparison tool, accepts a species, a list of probes, POs and plots the profiles for the selected
    """
    form = ProfileComparisonForm(request.form)
    form.populate_form()

    if request.method == 'POST':
        species_id = request.form.get('species_id')
        selected_species = db.session.get(Species, species_id)
        #po_choices = [(sample_po.po_id, PlantOntology.query.get(sample_po.po_id).po_class) \
        #              for sample_po in selected_species.po_associations.all()]
        #form.po_ids.choices = list(set(po_choices))
        terms = request.form.get('probes').split()
        normalize = True if request.form.get('normalize') == 'y' else False

        probes = terms

        # also do search by gene ID
        sequences = Sequence.query.filter(Sequence.name.in_(terms)).all()

        for s in sequences:
            for ep in s.expression_profiles:
                probes.append(ep.probe)

        # make probe list unique
        probes = list(set(probes))

        # get max 51 profiles, only show the first 50 (the extra one is fetched to throw the warning)
        profiles = ExpressionProfile.get_profiles(species_id, probes, limit=51)

        not_found = [p.lower() for p in probes]
        for p in profiles:
            with contextlib.suppress(ValueError):
                not_found.remove(p.probe.lower())

            with contextlib.suppress(ValueError):
                not_found.remove(p.sequence.name.lower())

        if len(not_found) > 0:
            flash("Couldn't find profile for: %s" % ", ".join(not_found), "warning")

        if len(profiles) > 50:
            flash(Markup(("To many profiles in this cluster only showing the <strong>first 50</strong>. <br />" +
                          "<strong>Note:</strong> The <a href='%s'>heatmap</a> can be used to with more genes and " +
                          "allows downloading the data for local analysis.") % url_for('heatmap.heatmap_main')),
                  'warning')

        # Get json object for chart
        profile_chart = prepare_profiles(profiles[:50], normalize,
                                         ylabel='TPM' + (' (normalized)' if normalize == 1 else ''))
        peco_profile_chart = prepare_profiles(profiles[:50], normalize,
                                         ylabel='TPM' + (' (normalized)' if normalize == 1 else ''), peco=True)

        # Get table in base64 format for download
        data = base64.encodebytes(prepare_profiles_download(profiles[:50], normalize).encode('utf-8'))

        return render_template("expression_profile_comparison.html",
                               profiles=json.dumps(profile_chart), peco_profiles=json.dumps(peco_profile_chart), form=form, data=data.decode('utf-8'))
    else:
        profiles = ExpressionProfile.query.filter(ExpressionProfile.sequence_id is not None).order_by(ExpressionProfile.species_id).limit(5).all()

        example = {
            'species_id': None,
            'probes': None
        }

        if len(profiles) > 0:
            example['species_id'] = profiles[0].species_id
            example['probes'] = ' '.join([p.sequence.name for p in profiles])

        return render_template("expression_profile_comparison.html", form=form, example=example)


@profile_comparison.route('/get_species_sample_lit/<species_id>')
def get_sample_lit(species_id):
    
    lit_info = SampleLitAssociation.query.with_entities(SampleLitAssociation.literature_id).filter_by(species_id=species_id).distinct().all()

    literatureArray = []
    literature_ids = []

    for lit_id in lit_info:
        lit_author = LiteratureItem.query.get(lit_id).author_names
        lit_year = LiteratureItem.query.get(lit_id).public_year
        if lit_id in literature_ids:
            continue
        else:
            literature_ids.append(lit_id)
        litObj = {}
        litObj['id'] = lit_id
        litObj['publication_detail'] = f'{lit_author} ({lit_year})'
        literatureArray.append(litObj)
    
    return jsonify({'literatures': literatureArray})