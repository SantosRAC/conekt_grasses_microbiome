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
    from conekt.controllers.expression_cluster import expression_cluster
    from conekt.controllers.expression_profile import expression_profile
    from conekt.controllers.expression_network import expression_network
    # from conekt.controllers.search import search
    # TODO: add search to configure_blueprints after Solr is up and running
    from conekt.controllers.help import help
    from conekt.controllers.heatmap import heatmap
    from conekt.controllers.profile_comparison import profile_comparison
    from conekt.controllers.custom_network import custom_network
    from conekt.controllers.graph_comparison import graph_comparison
    from conekt.controllers.clade import clade
    from conekt.controllers.ecc import ecc
    from conekt.controllers.specificity_comparison import specificity_comparison
    from conekt.controllers.admin.controls import admin_controls
    from conekt.controllers.tree import tree
    from conekt.controllers.study import study
    from conekt.controllers.microbiome.asvs_profile import asvs_profile

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
    app.register_blueprint(expression_cluster, url_prefix='/cluster')
    app.register_blueprint(expression_profile, url_prefix='/profile')
    app.register_blueprint(expression_network, url_prefix='/network')
    #app.register_blueprint(search, url_prefix='/search')
    # TODO: add URL after configuring Solr as the main search engine
    app.register_blueprint(help, url_prefix='/help')
    app.register_blueprint(heatmap, url_prefix='/heatmap')
    app.register_blueprint(profile_comparison, url_prefix='/profile_comparison')
    app.register_blueprint(custom_network, url_prefix='/custom_network')
    app.register_blueprint(graph_comparison, url_prefix='/graph_comparison')
    app.register_blueprint(clade, url_prefix='/clade')
    app.register_blueprint(ecc, url_prefix='/ecc')
    app.register_blueprint(specificity_comparison, url_prefix='/specificity_comparison')
    app.register_blueprint(tree, url_prefix='/tree')
    app.register_blueprint(asvs_profile, url_prefix='/asvs_profile')


def configure_admin_panel(app):
    # Admin panel
    LOGIN_ENABLED = app.config['LOGIN_ENABLED']
    if LOGIN_ENABLED:
        from conekt.controllers.admin.views import MyAdminIndexView

        from conekt.controllers.admin.views.ecc import ECCView
        from conekt.controllers.admin.views.sequences import AddSequenceDescriptionsView
        from conekt.controllers.admin.views.expression_profiles import AddExpressionProfilesView
        from conekt.controllers.admin.views.expression_networks import AddCoexpressionNetworkView
        from conekt.controllers.admin.views.expression_networks import ExpressionNetworkMethodAdminView
        from conekt.controllers.admin.views.expression_specificity import AddSpecificityView
        from conekt.controllers.admin.views.expression_specificity import ConditionTissueAdminView
        from conekt.controllers.admin.views.expression_specificity import ExpressionSpecificityMethodAdminView
        from conekt.controllers.admin.views.functional_data import AddInterProView
        from conekt.controllers.admin.views.functional_data import AddGOView
        from conekt.controllers.admin.views.functional_data import AddCAZYmeView
        from conekt.controllers.admin.views.functional_data import AddFunctionalDataView
        from conekt.controllers.admin.views.functional_data import GOEnrichmentView
        from conekt.controllers.admin.views.functional_data import PredictGOView
        from conekt.controllers.admin.views.taxonomy import AddTaxonomyView
        from conekt.controllers.admin.views.families import AddFamiliesView, AddFamilyAnnotationView
        from conekt.controllers.admin.views.families import GeneFamilyMethodAdminView
        from conekt.controllers.admin.views.samples import AddSamplesView
        from conekt.controllers.admin.views.species import AddSpeciesView
        from conekt.controllers.admin.views.species import SpeciesAdminView
        from conekt.controllers.admin.views.trees import AddTreesView
        from conekt.controllers.admin.views.expression_clusters import BuildNeighorhoodToClustersView
        from conekt.controllers.admin.views.expression_clusters import BuildCoexpressionClustersView
        from conekt.controllers.admin.views.expression_clusters import AddCoexpressionClustersView
        from conekt.controllers.admin.views.expression_clusters import ClusterSimilaritiesView
        from conekt.controllers.admin.views.expression_clusters import CoexpressionClusteringMethodAdminView
        from conekt.controllers.admin.views.clades import AddCladesView
        from conekt.controllers.admin.views.clades import CladesAdminView
        from conekt.controllers.admin.views.xrefs import AddXRefsFamiliesView
        from conekt.controllers.admin.views.xrefs import AddXRefsView
        from conekt.controllers.admin.views.controls import ControlsView
        from conekt.controllers.admin.views.news import NewsAdminView
        from conekt.controllers.admin.views.trees import TreeMethodAdminView
        from conekt.controllers.admin.views.trees import ReconcileTreesView
        from conekt.controllers.admin.views.ontology import AddOntologyView
        from conekt.controllers.admin.views.asvs import AddASVSView
        from conekt.controllers.admin.views.study import BuildStudyView

        from conekt.models.users import User
        from conekt.models.species import Species
        from conekt.models.gene_families import GeneFamilyMethod
        from conekt.models.expression.coexpression_clusters import CoexpressionClusteringMethod
        from conekt.models.expression.networks import ExpressionNetworkMethod
        from conekt.models.expression.specificity import ExpressionSpecificityMethod
        from conekt.models.condition_tissue import ConditionTissue
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
        admin.add_view(AddCoexpressionNetworkView(name='Coexpression network',
                                                  endpoint='admin_add_coexpression_network',
                                                  url='add/coexpression_network/', category='Add Expression'))
        admin.add_view(AddCoexpressionClustersView(name='Coexpression clusters',
                                                   endpoint='admin_add_coexpression_clusters',
                                                   url='add/coexpression_clusters/', category='Add Expression'))
        admin.add_view(AddSpecificityView(name='Expression Specificity',
                                          endpoint='admin_add_expression_specificity',
                                          url='add/expression_specificity/', category='Add'))

        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Add')
        admin.add_menu_item(MenuLink("Comparative Genomics", class_name="disabled", url="#"), target_category='Add')

        admin.add_view(AddFamiliesView(name='Gene Families',
                                       endpoint='admin_add_families',
                                       url='add/families/', category='Add'))

        admin.add_view(AddTreesView(name='Trees',
                                    endpoint='admin_add_trees',
                                    url='add/trees/', category='Add'))

        admin.add_view(AddCladesView(name='Clades',
                                     endpoint='admin_add_clades',
                                     url='add/clades/', category='Add'))

        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Add')
        admin.add_menu_item(MenuLink("Misc.", class_name="disabled", url="#"), target_category='Add')

        admin.add_view(AddXRefsView(name='XRefs Genes',
                                    endpoint='admin_add_xrefs',
                                    url='add/xrefs/', category='Add'))

        admin.add_view(AddXRefsFamiliesView(name='XRefs Families',
                                            endpoint='admin_add_xrefs_families',
                                            url='add/xrefs_families/', category='Add'))

        # Add Microbiome data
        admin.add_menu_item(MenuLink("Microbiome", class_name="disabled", url="#"), target_category='Add Microbiome Data')
        admin.add_view(AddASVSView(name='ASVs',
                                                 endpoint='admin_add_asvs',
                                                 url='add/asvs/', category='Add Microbiome Data'))

        # Build Menu
        admin.add_view(BuildStudyView(name='Study',
                                               endpoint='admin_build_study',
                                               url='build/study/', category='Build'))
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Build')
        admin.add_menu_item(MenuLink("Update Counts", url="/admin_controls/update/counts", class_name="confirmation"),
                            target_category='Build')
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Build')
        admin.add_menu_item(MenuLink("Assign Clades", url="/admin_controls/update/clades", class_name="confirmation"),
                            target_category='Build')

        admin.add_view(AddFamilyAnnotationView(name='Family-wise annotation',
                                               endpoint='admin_add_family_annotation',
                                               url='build/family_annotation/', category='Build'))

        admin.add_view(ReconcileTreesView(name='Reconcile Trees', endpoint='admin_reconcile_trees',
                                          url='build/reconciled_trees', category='Build'))

        admin.add_view(ECCView(name='Expression Context Conservations (ECC)', endpoint='admin_ecc',
                               url='build/ecc/', category='Build'))
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Build')
        admin.add_menu_item(MenuLink("Co-expression Clusters", class_name="disabled", url="#"), target_category='Build')

        admin.add_view(ClusterSimilaritiesView(name='Cluster Similarities', endpoint='admin_clustersimilarities',
                                               url='build/cluster_similarities/',
                                               category='Build'))
        admin.add_view(GOEnrichmentView(name='Cluster GO Enrichment', endpoint='admin_goenrichment',
                                        url='build/go_enrichment/',
                                        category='Build'))
        admin.add_view(BuildCoexpressionClustersView(name='HCCA Clusters',
                                                     endpoint='admin_build_hcca_clusters',
                                                     url='build/hcca_clusters/', category='Build'))
        admin.add_view(BuildNeighorhoodToClustersView(name='Neighborhood to clusters',
                                                      endpoint='admin_build_neighborhood_to_clusters',
                                                      url='build/neighborhood_to_clusters/', category='Build'))
        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Build')
        admin.add_view(PredictGOView(name='Predict GO from neighborhood', endpoint='admin_predict_go',
                                     url='predict/go', category='Build'))

        # Control panel
        admin.add_view(ControlsView(name='Controls', url='controls/'))

        # CRUD for various database tables
        admin.add_view(NewsAdminView(News, db.session,
                                     endpoint='admin_news',
                                     url='news', category='Browse'))
        admin.add_view(SpeciesAdminView(Species, db.session, url='species', category='Browse'))
        admin.add_view(CladesAdminView(Clade, db.session, url='clades', category='Browse', name='Clades'))
        admin.add_view(ConditionTissueAdminView(ConditionTissue, db.session, url='condition_tissue/',
                                                category="Browse", name='Condition to Tissue'))

        admin.add_menu_item(MenuLink("------------", class_name="divider", url='#'), target_category='Browse')
        admin.add_menu_item(MenuLink("Methods", class_name="disabled", url="#"), target_category='Browse')

        admin.add_view(GeneFamilyMethodAdminView(GeneFamilyMethod, db.session, url='families', category="Browse",
                                                 name='Gene Families'))
        admin.add_view(TreeMethodAdminView(TreeMethod, db.session, url='trees', category="Browse",
                                           name='Tree Methods'))
        #admin.add_view(ExpressionNetworkMethodAdminView(ExpressionNetworkMethod, db.session, url='networks',
        #                                                category="Browse", name='Expression Networks'))
        #admin.add_view(CoexpressionClusteringMethodAdminView(CoexpressionClusteringMethod, db.session, url='clusters',
        #                                                     category="Browse", name='Coexpression Clustering'))
        #admin.add_view(ExpressionSpecificityMethodAdminView(ExpressionSpecificityMethod, db.session, url='specificity',
        #                                                    category="Browse", name='Expression Specificity'))


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
