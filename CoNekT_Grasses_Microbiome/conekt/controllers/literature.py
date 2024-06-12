from flask import Blueprint, render_template, g, flash, redirect, url_for

from conekt import db, cache

from conekt.models.literature import LiteratureItem
from conekt.models.microbiome.operational_taxonomic_unit import OperationalTaxonomicUnit, OperationalTaxonomicUnitMethod

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


@literature.route('/lit_otus/<literature_id>/')
@literature.route('/lit_otus/<literature_id>/<int:page>')
@cache.cached()
def literature_otus(literature_id, page=1):
    """
    Returns a table with OTUs for the selected literature item (paper, book, book chapter)

    :param literature_id: Internal ID of the literature item
    :param page: Page number
    """

    otu_methods = OperationalTaxonomicUnitMethod.query.filter_by(literature_id=int(literature_id)).all()

    print(literature_id, type(literature_id), '\n\n\n\n\n\n\n\n\n')
    print([otu_method.id for otu_method in otu_methods], '\n\n\n\n\n\n\n\n\n')

    otus = OperationalTaxonomicUnit.query.filter(OperationalTaxonomicUnit.method_id.in_([otu_method.id for otu_method in otu_methods])).paginate(page=page, per_page=g.page_items, error_out=False).items

    return render_template('pagination/microbiome/otus.html', otus=otus)