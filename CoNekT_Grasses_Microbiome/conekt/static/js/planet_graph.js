/*global $, cytoscape, document, graph_data, window, generate_legend, writeXGMML, writeSVG, Pablo, svg_legend */
var cy;
var initial_json;

function select_neighborhood(ev, node_name) {
    ev.preventDefault();

    // Select all nodes in the neighborhood
    cy.nodes('[name = \'' + node_name + '\']').neighborhood().select();

    // Close tooltip
    $('div.qtip:visible').qtip('hide');
};

function click_edge(ev) {
    ev.preventDefault();
    // Reset all nodes in the legend
    svg_legend.find(".legend_node").transform('scale', null);
};

$(function () { // on dom ready
    'use strict';
    var url = $('#cy').attr("json"),
        cycss_url = $('#cy').attr("cycss");

    cy = cytoscape({
        container: document.getElementById('cy'),
        style: $.get(cycss_url),
        wheelSensitivity: 0.333,
        elements: url !== undefined ? $.getJSON(url) : graph_data,
        layout: {
            name: 'cose',
            padding: 60,
            minNodeSpacing: 30,
            avoidOverlap: false
        },
        ready: function () {
            window.cy = this;

            initial_json = JSON.stringify(cy.json(), null, '\t');

            cy.nodes('[^compound]').forEach(function (n) {
                // code to add tooltips to the selected node
                var content = [
                    {
                        value: '<strong>Name:</strong> ' + n.data('name')
                    }];

                if (n.data('gene_link') !== undefined) {
                    content.push({value: '<strong><a href=' + n.data('gene_link') + '">Link to Gene Page</a></strong>'});
                }

                if (n.data('otu_link') !== undefined) {
                    content.push({value: '<strong><a href=' + n.data('otu_link') + '">Link to OTU Page</a></strong>'});
                }

                n.qtip({
                    content: content.map(function (item) {
                        return item.value;
                    }).join('<br />\n'),
                    position: {
                        my: 'bottom center',
                        at: 'top center'
                    },
                    style: {
                        classes: 'qtip-bootstrap',
                        tip: {
                            width: 16,
                            height: 8
                        }
                    }
                });
            }); /* End nodes.forEach */

            cy.edges('[^correlation]').forEach(function (e) {
                // code to add tooltips to the selected node
                var content = [{
                        value: 'Edge: ' + e.data('source_name') + ' and ' + e.data('target_name')
                    }];

                if (e.data('link_cc') !== undefined) {
                    if (e.data('link_cc') !== null) {
                        content.push({ value: 'Correlation Coef.: ' + e.data('link_cc').toFixed(3) });
                    }
                }

                e.qtip({
                    content: content.map(function (item) {
                        return item.value;
                    }).join('<br />\n'),
                    position: {
                        my: 'bottom center',
                        at: 'center center'
                    },
                    style: {
                        classes: 'qtip-bootstrap',
                        tip: {
                            width: 16,
                            height: 8
                        }
                    }
                });
            }); // end cy.edges.forEach...

            /* Enable click events */
            cy.edges().on("click", function(ev) {
                click_edge(ev);
            });

             cy.on("click", function(ev) {
                click_edge(ev);
            });

            cy.style()
                .selector('edge[link_cc > 0]')
                .style({
                    'line-color': 'green',   // Color for positive edges
                    'target-arrow-color': 'green'
                })
                .selector('edge[link_cc < 0]')
                .style({
                    'line-color': 'red',     // Color for negative edges
                    'target-arrow-color': 'red'
                })
                .update();

            /* Make cursor pointer when hovering over*/
            cy.on('mouseover', 'node', function (evt) {
                        $('html,body').css('cursor', 'pointer');
                    } );

            cy.on('mouseout', 'node', function (evt) {
                        $('html,body').css('cursor', 'default');
                    });

            /* Make cursor pointer when hovering over*/
            cy.on('mouseover', 'edge', function (evt) {
                        $('html,body').css('cursor', 'pointer');
                    } );

            cy.on('mouseout', 'edge', function (evt) {
                        $('html,body').css('cursor', 'default');
                    });

            $('.cy-node-color[attr="link_cc"]').click();

            $('#loading').addClass('loaded');
            $('#legend').show();

        }
    });

    $('.cy-node-shape').click(function (ev) {
        ev.preventDefault();
        $(this).closest('.cy-option-menu').find('.cy-node-shape').each(function () {
            cy.nodes('[^compound]').removeClass($(this).attr('attr'));
        });
        cy.nodes('[^compound]').addClass($(this).attr('attr'));
    });

    $('.cy-node-hide').click(function (ev) {
        ev.preventDefault();
        cy.nodes('[tag="hideable"]').addClass('hidden');
        $(this).hide();
        $('.cy-node-show').show();
    });

    $('.cy-node-show').click(function (ev) {
        ev.preventDefault();
        cy.nodes('[tag="hideable"]').removeClass('hidden');
        $(this).hide();
        $('.cy-node-hide').show();
    });

    $('.cy-edge-color').click(function (ev) {
        ev.preventDefault();
        $(this).closest('.cy-option-menu').find('.cy-edge-color').each(function () {
            cy.edges('[^correlation]').removeClass($(this).attr('attr'));
        });
        cy.edges('[^correlation]').addClass($(this).attr('attr'));
    });

    $('.cy-edge-width').click(function (ev) {
        ev.preventDefault();
        $(this).closest('.cy-option-menu').find('.cy-edge-width').each(function () {
            cy.edges('[^correlation]').removeClass($(this).attr('attr'));
        });

        cy.edges('[^correlation]').addClass($(this).attr('attr'));
    });

    $('.cy-layout').click(function (ev) {
        ev.preventDefault();
        var layout = $(this).attr('layout');

        cy.layout({name: layout,
                   padding: 60,
                   minNodeSpacing: 30,
                   animate: true,
                   avoidOverlap: false,
                   animationThreshold: 250,
                   //cose settings
                   nodeOverlap: 8,
                   idealEdgeLength: 32,
                   edgeElasticity: 32,
                   numIter: 1000,
                   maxSimulationTime: 2000,
                   lengthFactor: 100
                   });
    });

    $("#cy-search").click(function (ev) {
        ev.preventDefault();
        var term = $("#cy-search-term").val().trim().toLowerCase(),
            search_url = $(this).attr('search-url'),
            valid_genes = [];

        cy.nodes('[^compound]').toggleClass('found', false);
        $('#search_logo').hide();
        $('#search_spinner').show();
        $.getJSON(search_url + term, function (data) {
            var i = 0;
            for (i = 0; i < data.length; i += 1) {
                valid_genes.push(data[i]);
            }
        }).error(function() {
            $('#search_logo').show();
            $('#search_spinner').hide();
        }).done(function () {
            if (term !== '') {
                cy.nodes('[^compound]').each(function (i, node) {
                    if (node.data('name').toLowerCase() === term) {
                        node.toggleClass('found');
                    }
                });
            }
        }).done(function() {
            $('#search_logo').show();
            $('#search_spinner').hide();
        });
    });

    $('#cy-reset').on('click', function (ev) {
        ev.preventDefault();
        cy.animate({
            fit: {
                eles: cy.elements(),
                padding: 5
            },
            duration: 500
        });
    });
}); // end on dom ready