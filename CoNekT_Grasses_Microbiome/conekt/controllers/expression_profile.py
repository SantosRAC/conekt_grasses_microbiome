import json

from flask import Blueprint, redirect, url_for, render_template, Response, request, current_app, send_from_directory
from sqlalchemy.orm import undefer

from statistics import mean
import sys
import tempfile
import os

from conekt import cache
from conekt.helpers.chartjs import prepare_expression_profile, prepare_profile_comparison
from conekt.forms.export_condition import ExportConditionForm

expression_profile = Blueprint('expression_profile', __name__)


@expression_profile.route('/')
def expression_profile_overview():
    """
    For lack of a better alternative redirect users to the main page
    """
    return redirect(url_for('main.screen'))



@expression_profile.route('/export/get_file/<name>')
def export_expression_levels_file(name):
    return send_from_directory(current_app.config["TMP_DIR"],
        name,
        as_attachment=True,
        attachment_filename="expression.tab",)

