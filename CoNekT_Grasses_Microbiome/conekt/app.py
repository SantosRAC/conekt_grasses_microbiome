"""
Everything that needs to be set up to get flask running is initialized in this file.

  * set up and configure the app

  * configure extensions (db, compress, ...)

  * load all controllers and register their blueprints to a subdomain

  * Note: as long as models are used by a controller they are loaded and included in create_db !

  * add admin panel

  * set up global things like the search form and custom 403/404 error messages
"""
from flask import Flask, render_template, g, request, url_for, flash, redirect
from flask_admin.menu import MenuLink
from flask_login import current_user
from flask_admin import Admin

from conekt.extensions import db, login_manager, cache, htmlmin, \
    blast_thread, compress, migrate, csrf

import coloredlogs


def create_app(config):
    # Set up app, database and login manager before importing models and controllers
    # Important for db_create script

    app = Flask(__name__)

    coloredlogs.install()

    with app.app_context():
    
        app.config.from_object(config)
        configure_extensions(app)
        configure_blueprints(app)
        configure_admin_panel(app)
        configure_error_handlers(app)
        configure_hooks(app)

        db.create_all()

    return app


def configure_extensions(app):
    db.app = app
    db.init_app(app)

    # Enable Solr
    # TODO: implement Solr as the 

    # Enable login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Enable cach
    cache.init_app(app)

    # Enable Compress
    compress.init_app(app)

    # Enable HTMLMIN
    htmlmin.init_app(app)

    # Enable CSRF Protect globally
    csrf.init_app(app)

    migrate.init_app(app, db=db)

    BLAST_ENABLED = app.config['BLAST_ENABLED']

    # Enable BLAST
    if BLAST_ENABLED:
        blast_thread.init_app(app)

    from conekt.models.users import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        return render_template('error/403.html'), 403


def configure_blueprints(app):
    # Import controllers and register as blueprint
    from conekt.controllers.main import main
    from conekt.controllers.auth import auth, no_login
    from conekt.controllers.blast import blast
    from conekt.controllers.sequence import sequence
    from conekt.controllers.species import species
    from conekt.controllers.go import go
    from conekt.controllers.interpro import interpro
    from conekt.controllers.cazyme import cazyme
    from conekt.controllers.family import family
    from conekt.controllers.expression_profile import expression_profile
    from conekt.controllers.search import search
    # TODO: Configure Solr to replace Whoosh !
    from conekt.controllers.help import help
    from conekt.controllers.clade import clade
    from conekt.controllers.admin.controls import admin_controls
    from conekt.controllers.tree import tree
    from conekt.controllers.study import study
    from conekt.controllers.profile_comparison import profile_comparison
    from conekt.controllers.microbiome.asvs_profile import asvs_profile
    from conekt.controllers.microbiome.otu_profiles import otus_profile
    from conekt.controllers.microbiome.otus import otu
    from conekt.controllers.omics_integration.profile_correlations import profile_correlations
    from conekt.controllers.literature import literature
    from conekt.controllers.omics_integration.custom_expression_microbiome_network import custom_network

    LOGIN_ENABLED = app.config['LOGIN_ENABLED']
    BLAST_ENABLED = app.config['BLAST_ENABLED']

    app.register_blueprint(main)
    if LOGIN_ENABLED:
        app.register_blueprint(auth, url_prefix='/auth')
        app.register_blueprint(admin_controls, url_prefix='/admin_controls')
    else:
        app.register_blueprint(no_login, url_prefix='/auth')
        app.register_blueprint(no_login, url_prefix='/admin_controls')

    if BLAST_ENABLED:
        app.register_blueprint(blast, url_prefix='/blast')

    app.register_blueprint(sequence, url_prefix='/sequence')
    app.register_blueprint(species, url_prefix='/species')
    app.register_blueprint(study, url_prefix='/study')
    app.register_blueprint(go, url_prefix='/go')
    app.register_blueprint(interpro, url_prefix='/interpro')
    app.register_blueprint(cazyme, url_prefix='/cazyme')
    app.register_blueprint(family, url_prefix='/family')
    app.register_blueprint(expression_profile, url_prefix='/profile')
    app.register_blueprint(custom_network, url_prefix='/custom_network')
    app.register_blueprint(search, url_prefix='/search')
    # TODO: add URL after configuring Solr as the main search engine
    app.register_blueprint(help, url_prefix='/help')
    app.register_blueprint(profile_comparison, url_prefix='/profile_comparison')
    app.register_blueprint(otu, url_prefix='/otu')
    app.register_blueprint(asvs_profile, url_prefix='/asvs_profile')
    app.register_blueprint(otus_profile, url_prefix='/otus_profile')
    app.register_blueprint(profile_correlations, url_prefix='/profile_correlations')
    app.register_blueprint(literature, url_prefix='/literature')


def configure_admin_panel(app):
    # Admin panel
    LOGIN_ENABLED = app.config['LOGIN_ENABLED']
    if LOGIN_ENABLED:
        from conekt.controllers.admin.views import MyAdminIndexView

        from conekt.controllers.admin.views.sequences import AddSequenceDescriptionsView
        from conekt.controllers.admin.views.expression_profiles import AddExpressionProfilesView
        from conekt.controllers.admin.views.functional_data import AddInterProView
        from conekt.controllers.admin.views.functional_data import AddGOView
        from conekt.controllers.admin.views.functional_data import AddCAZYmeView
        from conekt.controllers.admin.views.functional_data import AddFunctionalDataView
        from conekt.controllers.admin.views.taxonomy import AddTaxonomyView
        from conekt.controllers.admin.views.families import AddFamilyAnnotationView
        from conekt.controllers.admin.views.families import GeneFamilyMethodAdminView
        from conekt.controllers.admin.views.samples import AddSamplesView
        from conekt.controllers.admin.views.species import AddSpeciesView
        from conekt.controllers.admin.views.species import SpeciesAdminView
        from conekt.controllers.admin.views.controls import ControlsView
        from conekt.controllers.admin.views.news import NewsAdminView
        from conekt.controllers.admin.views.ontology import AddOntologyView
        from conekt.controllers.admin.views.asvs import AddASVSView
        from conekt.controllers.admin.views.otus import AddOTUSView
        from conekt.controllers.admin.views.otus import AddOTUClassificationView
        from conekt.controllers.admin.views.study import BuildStudyView
        from conekt.controllers.admin.views.omics_integration.expression_microbiome_correlations import BuildCorrelationsView

        from conekt.models.users import User
        from conekt.models.species import Species
        from conekt.models.gene_families import GeneFamilyMethod
        from conekt.models.clades import Clade
        from conekt.models.news import News
        from conekt.models.trees import TreeMethod
        from conekt.models.ontologies import PlantOntology

        admin = Admin(template_mode='bootstrap3', base_template='admin/my_base.html')

        admin.init_app(app, index_view=MyAdminIndexView(template='admin/home.html'))

        # Add views for External data
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Add External')
        admin.add_view(AddTaxonomyView(name='Taxonomy', endpoint='admin_add_taxonomy', url='add/taxonomy/', category='Add External'))
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Add External')
        admin.add_menu_item(MenuLink("Functional Annotation", class_name="disabled", url="#"), target_category='Add External')
        admin.add_view(AddFunctionalDataView(name='Functional Data',
                                             endpoint='admin_add_functional_data',
                                             url='add/functional_data/', category='Add External'))        
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Add External')
        admin.add_menu_item(MenuLink("Ontology", class_name="disabled", url="#"), target_category='Add External')
        admin.add_view(AddOntologyView(name='Ontology definitions',
                                                 endpoint='admin_add_ontology',
                                                 url='add/ontology/', category='Add External'))

        # Add Species information
        admin.add_view(AddSpeciesView(name='Species', endpoint='admin_add_species', url='add/species/', category='Add Species'))
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Add Species')
        admin.add_view(AddSamplesView(name='Samples', endpoint='admin_add_samples', url='add/samples/', category='Add Species'))
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Add Species')
        admin.add_view(AddSequenceDescriptionsView(name='Sequence Descriptions',
                                                   endpoint='admin_add_sequence_descriptions',
                                                   url='add/sequence_descriptions/', category='Add Species'))
        admin.add_view(AddGOView(name='GO Genes',
                                 endpoint='admin_add_go_sequences',
                                 url='add/go/', category='Add Species'))
        admin.add_view(AddInterProView(name='InterPro Genes',
                                       endpoint='admin_add_interpro_sequences',
                                       url='add/interpro/', category='Add Species'))
        admin.add_view(AddCAZYmeView(name='CAZYme Genes',
                                    endpoint='admin_add_cazyme_sequences',
                                    url='add/cazyme/', category='Add Species'))

        # Add views for Expression data
        admin.add_menu_item(MenuLink("Expression", class_name="disabled", url="#"), target_category='Add Expression')
        admin.add_view(AddExpressionProfilesView(name='Expression profiles',
                                                 endpoint='admin_add_expression_profiles',
                                                 url='add/expression_profiles/', category='Add Expression'))

        # Add Microbiome data
        admin.add_menu_item(MenuLink("Microbiome", class_name="disabled", url="#"), target_category='Add Microbiome Data')
        admin.add_view(AddASVSView(name='ASVs',
                                                 endpoint='admin_add_asvs',
                                                 url='add/asvs/', category='Add Microbiome Data'))
        admin.add_view(AddOTUSView(name='OTUs',
                                                 endpoint='admin_add_otus',
                                                 url='add/otus/', category='Add Microbiome Data'))
        admin.add_view(AddOTUClassificationView(name='OTU Classification',
                                                 endpoint='admin_add_otu_classification',
                                                 url='add/otu_classification/', category='Add Microbiome Data'))

        # Build Menu
        admin.add_view(BuildStudyView(name='Study',
                                               endpoint='admin_build_study',
                                               url='build/study/', category='Build'))
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Build')
        admin.add_menu_item(MenuLink("Integration of RNAseq and Metataxonomics", class_name="disabled", url="#"), target_category='Build')
        admin.add_view(BuildCorrelationsView(name='Build RNAseq - Metataxonomics Profile Correlations', endpoint='admin_build_rnametataxcor',
                                     url='build/exp_metatax_correlations', category='Build'))

        # Control panel
        admin.add_view(ControlsView(name='Controls', url='controls/'))

        # CRUD for various database tables
        admin.add_view(NewsAdminView(News, db.session,
                                     endpoint='admin_news',
                                     url='news', category='Browse'))
        admin.add_view(SpeciesAdminView(Species, db.session, url='species', category='Browse'))
        
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Browse')
        admin.add_menu_item(MenuLink("Methods", class_name="disabled", url="#"), target_category='Browse')

        admin.add_view(GeneFamilyMethodAdminView(GeneFamilyMethod, db.session, url='families', category="Browse",
                                                 name='Gene Families'))



def configure_error_handlers(app):
    # Custom error handler for 404 errors

    from flask_wtf.csrf import CSRFError

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash("Could not handle request, CSRF token has expired. Please try again...", "warning")
        return redirect(url_for('main.screen'))

    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template('error/405.html'), 405

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.html'), 404

    @app.errorhandler(403)
    def access_denied(e):
        next_page = request.url_rule
        if not current_user.is_authenticated:
            flash("Log in first...", "info")
            return redirect(url_for('auth.login', next=next_page))
        else:
            flash("Not permitted! Admin rights required.", "warning")
            return render_template('error/403.html'), 403


def configure_hooks(app):
    # Register form for basic searches, needs to be done here as it is included on every page!
    from conekt.forms.search import BasicSearchForm

    LOGIN_ENABLED = app.config['LOGIN_ENABLED']
    BLAST_ENABLED = app.config['BLAST_ENABLED']
    TWITTER_HANDLE = app.config['TWITTER_HANDLE'] if 'TWITTER_HANDLE' in app.config.keys() else None
    TUTORIAL_URL = app.config['TUTORIAL_URL'] if 'TUTORIAL_URL' in app.config.keys() else None
    IMPRINT = app.config['IMPRINT_URL'] if 'IMPRINT_URL' in app.config.keys() else None
    PRIVACY = app.config['PRIVACY_POLICY_URL'] if 'PRIVACY_POLICY_URL' in app.config.keys() else None

    @app.before_request
    def before_request():
        g.login_enabled = LOGIN_ENABLED
        g.blast_enabled = BLAST_ENABLED
        g.search_form = BasicSearchForm()
        g.twitter_handle = TWITTER_HANDLE
        g.imprint = IMPRINT
        g.privacy = PRIVACY

        g.tutorial = TUTORIAL_URL

        g.page_items = 30

        g.debug = app.config['DEBUG'] if 'DEBUG' in app.config else False

        if 'GLOB_MSG' in app.config and app.config['GLOB_MSG'] is not None:
            g.msg = app.config['GLOB_MSG']
            g.msg_title = app.config['GLOB_MSG_TITLE'] if 'GLOB_MSG_TITLE' in app.config else 'info'
        else:
            g.msg = None
