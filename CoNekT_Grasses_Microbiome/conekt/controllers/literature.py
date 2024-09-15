from flask import Blueprint, render_template, g, flash, redirect, url_for

from conekt import db, cache

from conekt.models.literature import LiteratureItem

literature = Blueprint('literature', __name__)


@literature.route('/')
def literature_overview():
    """
    For lack of a better alternative redirect users to the main page
    """
    return redirect(url_for('main.screen'))


@literature.route('/view/<literature_id>')
@cache.cached()
def literature_view(literature_id):
    """
    Get a literature item based on the ID and show the details for this paper/book/book chapter.
    The description, which can be markdown is converted prior to adding it to the template.

    :param literature_id: ID of the literature to show
    """
    current_literature = db.session.get(LiteratureItem, literature_id)

    return render_template('literature.html', literature=current_literature)