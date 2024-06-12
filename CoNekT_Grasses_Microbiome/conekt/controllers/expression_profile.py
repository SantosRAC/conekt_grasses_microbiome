import json

from flask import Blueprint, redirect, url_for, render_template, Response, request, current_app, send_from_directory
from sqlalchemy.orm import undefer

from statistics import mean
import sys
import tempfile
import os

from conekt import cache
from conekt.helpers.chartjs import prepare_expression_profile, prepare_profile_comparison
from conekt.models.expression.profiles import ExpressionProfile
from conekt.forms.export_condition import ExportConditionForm

expression_profile = Blueprint('expression_profile', __name__)


@expression_profile.route('/')
def expression_profile_overview():
    """
    For lack of a better alternative redirect users to the main page
    """
    return redirect(url_for('main.screen'))


@expression_profile.route('/view/<profile_id>')
@cache.cached()
def expression_profile_view(profile_id):
    """
    Gets expression profile data from the database and renders it.

    :param profile_id: ID of the profile to show
    """
    current_profile = ExpressionProfile.query.get_or_404(profile_id)

    return render_template("expression_profile.html", profile=current_profile)


@expression_profile.route('/modal/<profile_id>')
@cache.cached()
def expression_profile_modal(profile_id):
    """
    Gets expression profile data from the database and renders it.

    :param profile_id: ID of the profile to show
    """
    current_profile = ExpressionProfile.query.get_or_404(profile_id)

    return render_template("modals/expression_profile.html", profile=current_profile)


@expression_profile.route('/find/<probe>')
@expression_profile.route('/find/<probe>/<species_id>')
@cache.cached()
def expression_profile_find(probe, species_id=None):
    """
    Gets expression profile data from the database and renders it.

    :param probe: Name of the probe
    :param species_id: Species ID is required to ensure a unique hit
    """
    current_profile = ExpressionProfile.query.filter_by(probe=probe)

    if species_id is not None:
        current_profile = current_profile.filter_by(species_id=species_id)

    first_profile = current_profile.first_or_404()

    return redirect(url_for('expression_profile.expression_profile_view', profile_id=first_profile.id))


@expression_profile.route('/download/plot/<profile_id>')
@cache.cached()
def expression_profile_download_plot(profile_id):
    """
    Generates a tab-delimited table for off-line use

    :param profile_id: ID of the profile to render
    """
    current_profile = ExpressionProfile.query.options(undefer('profile')).get_or_404(profile_id)
    print(current_profile.table)
    return Response(current_profile.table, mimetype='text/plain')


@expression_profile.route('/download/plot/<profile_id>/<condition_tissue_id>')
@cache.cached()
def expression_profile_download_tissue_plot(profile_id, condition_tissue_id):
    """
    Generates a tab-delimited table for off-line use

    :param profile_id: ID of the profile to render
    :param condition_tissue_id: ID of conversion table
    """
    current_profile = ExpressionProfile.query.options(undefer('profile')).get_or_404(profile_id)

    return Response(current_profile.tissue_table(condition_tissue_id))


@expression_profile.route('/json/plot/<profile_id>')
@cache.cached()
def expression_profile_plot_json(profile_id):
    """
    Generates a JSON object that can be rendered using Chart.js line plots

    :param profile_id: ID of the profile to render
    """
    current_profile = ExpressionProfile.query.options(undefer('profile')).get_or_404(profile_id)
    data = json.loads(current_profile.profile)

    plot = prepare_expression_profile(data, show_sample_count=True, ylabel='TPM')

    return Response(json.dumps(plot), mimetype='application/json')


@expression_profile.route('/json/plot/<profile_id>/<condition_tissue_id>')
@cache.cached()
def expression_profile_plot_tissue_json(profile_id, condition_tissue_id):
    """
    Generates a JSON object that can be rendered using Chart.js line plots

    :param profile_id: ID of the profile to render
    :param condition_tissue_id: ID of the condition to tissue conversion to be used
    """
    current_profile = ExpressionProfile.query.options(undefer('profile')).get_or_404(profile_id)
    data = current_profile.tissue_profile(condition_tissue_id)

    plot = prepare_expression_profile(data, ylabel='TPM')

    return Response(json.dumps(plot), mimetype='application/json')


@expression_profile.route('/json/compare_plot/<first_profile_id>/<second_profile_id>')
@expression_profile.route('/json/compare_plot/<first_profile_id>/<second_profile_id>/<int:normalize>')
@cache.cached()
def expression_profile_compare_plot_json(first_profile_id, second_profile_id, normalize=0):
    """
    Generates a JSON object with two profiles that can be rendered using Chart.js line plots

    :param first_profile_id:
    :param second_profile_id:
    :param normalize:
    :return:
    """
    first_profile = ExpressionProfile.query.options(undefer('profile')).get_or_404(first_profile_id)
    second_profile = ExpressionProfile.query.options(undefer('profile')).get_or_404(second_profile_id)
    data_first = json.loads(first_profile.profile)
    data_second = json.loads(second_profile.profile)

    plot = prepare_profile_comparison(data_first, data_second,
                                      (first_profile.probe, second_profile.probe),
                                      normalize=normalize,
                                      ylabel='TPM' + (' (normalized)' if normalize else ''))

    return Response(json.dumps(plot), mimetype='application/json')


@expression_profile.route('/export/get_file/<name>')
def export_expression_levels_file(name):
    return send_from_directory(current_app.config["TMP_DIR"],
        name,
        as_attachment=True,
        attachment_filename="expression.tab",)

