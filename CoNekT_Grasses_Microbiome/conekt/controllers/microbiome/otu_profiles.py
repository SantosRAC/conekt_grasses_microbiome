from flask import Blueprint, render_template

from conekt import cache
from conekt.models.microbiome.otu_profiles import OTUProfile

otus_profile = Blueprint('otus_profile', __name__)


@otus_profile.route('/view/<profile_id>')
@cache.cached()
def otu_profile_view(profile_id):
    """
    Gets OTU profile data from the database and renders it.

    :param profile_id: ID of the profile to show
    """
    current_profile = OTUProfile.query.get_or_404(profile_id)

    return render_template("otu_profile.html", profile=current_profile)