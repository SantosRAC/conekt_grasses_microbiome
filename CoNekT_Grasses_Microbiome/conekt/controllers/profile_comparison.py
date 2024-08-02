import json
import base64
import contextlib

from conekt import db
from flask import Blueprint, request, render_template, flash, url_for, jsonify
from sqlalchemy.orm import noload

from conekt import cache
from conekt.forms.profile_comparison import ProfileComparisonForm
from conekt.helpers.chartjs import prepare_profiles, prepare_profiles_download
from conekt.models.sequences import Sequence
from conekt.models.species import Species
from conekt.models.ontologies import PlantOntology
from conekt.models.relationships.sample_literature import SampleLitAssociation
from conekt.models.literature import LiteratureItem

profile_comparison = Blueprint('profile_comparison', __name__)


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