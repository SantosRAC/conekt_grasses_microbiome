import json

from flask import Blueprint, redirect, url_for, render_template, Response, request, current_app, send_from_directory
from sqlalchemy.orm import undefer

from statistics import mean
import sys
import tempfile
import os

from conekt import cache
from conekt.helpers.chartjs import prepare_expression_profile, prepare_profile_comparison
from conekt.models.expression.cross_species_profile import CrossSpeciesExpressionProfile
from conekt.models.condition_tissue import ConditionTissue
from conekt.models.expression.profiles import ExpressionProfile
from conekt.models.expression.networks import ExpressionNetwork
from conekt.models.expression.specificity import ExpressionSpecificityMethod
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

    expression_specificity_methods = ExpressionSpecificityMethod.query.filter(ExpressionSpecificityMethod.species_id == current_profile.species_id).all()

    tissues = []

    for esm in expression_specificity_methods:
        if esm.condition_tissue is not None:
            tissues.append({'id': esm.condition_tissue.id,
                            'name': esm.description,
                            'description': esm.condition_tissue.description})

    return render_template("expression_profile.html", profile=current_profile, tissues=tissues)


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


@expression_profile.route('/compare/<first_profile_id>/<second_profile_id>')
@expression_profile.route('/compare/<first_profile_id>/<second_profile_id>/<int:normalize>')
@cache.cached()
def expression_profile_compare(first_profile_id, second_profile_id, normalize=0):
    """
    Gets expression profile data from the database and renders it.

    :param first_profile_id: internal ID of the first profile
    :param second_profile_id: internal ID of the second profile
    :param normalize: 1 to normalize profiles (to max value), 0 to disable
    :return:
    """
    first_profile = ExpressionProfile.query.get_or_404(first_profile_id)
    second_profile = ExpressionProfile.query.get_or_404(second_profile_id)

    pcc = None
    hrr = None

    networks = ExpressionNetwork.query.filter(ExpressionNetwork.sequence_id == first_profile.sequence_id).all()

    for n in networks:
        data = json.loads(n.network)
        for link in data:
            if "gene_id" in link.keys() and link["gene_id"] == second_profile.sequence_id:
                if "link_pcc" in link.keys():
                    pcc = link["link_pcc"] if pcc is None or pcc < link["link_pcc"] else pcc
                if "hrr" in link.keys():
                    hrr = link["hrr"] if hrr is None or hrr > link["hrr"] else hrr

    return render_template("compare_profiles.html",
                           first_profile=first_profile,
                           second_profile=second_profile,
                           normalize=normalize,
                           pcc=pcc,
                           hrr=hrr)


@expression_profile.route('/compare_probes/<probe_a>/<probe_b>/<int:species_id>')
@expression_profile.route('/compare_probes/<probe_a>/<probe_b>/<int:species_id>/<int:normalize>')
@cache.cached()
def expression_profile_compare_probes(probe_a, probe_b, species_id, normalize=0):
    """
    Gets expression profile data from the database and renders it.

    :param probe_a: name of the first probe
    :param probe_b: name of the second probe
    :param species_id: internal id of the species the probes are linked with
    :param normalize: 1 to normalize profiles (to max value), 0 to disable
    :return:
    """
    first_profile = ExpressionProfile.query.filter_by(probe=probe_a).filter_by(species_id=species_id).first_or_404()
    second_profile = ExpressionProfile.query.filter_by(probe=probe_b).filter_by(species_id=species_id).first_or_404()

    pcc = None
    hrr = None

    networks = ExpressionNetwork.query.filter(ExpressionNetwork.sequence_id == first_profile.sequence_id).all()

    for n in networks:
        data = json.loads(n.network)
        for link in data:
            if "gene_id" in link.keys() and link["gene_id"] == second_profile.sequence_id:
                if "link_pcc" in link.keys():
                    pcc = link["link_pcc"] if pcc is None or pcc < link["link_pcc"] else pcc
                if "hrr" in link.keys():
                    hrr = link["hrr"] if hrr is None or hrr > link["hrr"] else hrr

    return render_template("compare_profiles.html",
                           probe_a=probe_a,
                           probe_b=probe_b,
                           first_profile=first_profile,
                           second_profile=second_profile,
                           species_id=species_id,
                           normalize=normalize,
                           pcc=pcc,
                           hrr=hrr)


# @expression_profile.route('/cross_species/')
# def expression_profile_cross_species():
#     """
#     DEBUG CODE
#     """
#     csep = CrossSpeciesExpressionProfile()
#
#     output = csep.get_data(*[78, 256593, 161407])
#
#     return Response(json.dumps(output))


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


def __generate(species_id, method_id, condition):
    """


    :param species_id: internal ID of species
    :param method_id: internal ID of the method
    :param condition: Condition to be exported
    :return: output
    """
    yield "Sequence\tAliases\tDescription\tAvg.Expression\tMin.Expression\tMax.Expression\n"

    profiles = ExpressionProfile.query.filter(ExpressionProfile.species_id == species_id). \
        filter(ExpressionProfile.sequence_id is not None). \
        options(undefer('profile')).order_by(ExpressionProfile.probe.asc()).all()

    condition_tissue = ConditionTissue.query. \
        filter(ConditionTissue.expression_specificity_method_id == method_id).first()

    condition_tissue_data = json.loads(condition_tissue.data) if condition_tissue is not None else None

    for p in profiles:
        try:
            data = json.loads(p.profile)
            if condition_tissue is None:
                # main profile is used, directly export values
                values = data["data"][condition]
            else:
                # summarized profile is selected, convert and export
                converted_profile = ExpressionProfile.convert_profile(condition_tissue_data,
                                                                      data, use_means=True)
                values = converted_profile["data"][condition]

            aliases = p.sequence.aliases if p.sequence.aliases is not None else ""
            description = p.sequence.description if p.sequence.description is not None else ""

            yield "%s\t%s\t%s\t%f\t%f\t%f\n" % (p.sequence.name, aliases, description, mean(values), min(values), max(values))

        except Exception as e:
            print("An error occured exporting a profile with conditions %s for species %d." % (condition, species_id),
                  file=sys.stderr)
            print(e, file=sys.stderr)


@expression_profile.route('/export/species', methods=['GET', 'POST'])
def export_expression_levels():
    """
    Will return a table with all (!) genes and their expression levels

    :return: either form with settings (on GET) or response with results (on POST)
    """
    form = ExportConditionForm(request.form)
    form.populate_form()

    if request.method == 'POST':
        species_id = int(request.form.get('species'))
        method_id = int(request.form.get('methods'))
        condition = request.form.get('conditions')

        _, filepath = tempfile.mkstemp(prefix='expr_', dir=current_app.config["TMP_DIR"])

        filename = os.path.basename(filepath)
        print(filepath, filename)

        with open(filepath, "w") as fout:
            for l in __generate(species_id, method_id, condition):
                print(l, end='', file=fout)

        return Response(json.dumps({"url": url_for('expression_profile.export_expression_levels_file', name=filename)}), mimetype='application/json')
    else:
        return render_template("export_condition.html", form=form)


@expression_profile.route('/export/get_file/<name>')
def export_expression_levels_file(name):
    return send_from_directory(current_app.config["TMP_DIR"],
        name,
        as_attachment=True,
        attachment_filename="expression.tab",)

