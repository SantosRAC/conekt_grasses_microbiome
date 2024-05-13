from flask import flash, url_for
from conekt.extensions import admin_required
from werkzeug.utils import redirect

from conekt.controllers.admin.controls import admin_controls


# TODO: add decorator for Solr
# TODO: create endpoint to reindex Solr (like previously done with Whooshee)
