/*global $, cytoscape, document, graph_data, window, generate_legend, writeXGMML, writeSVG, Pablo, svg_legend */
var cy;
var initial_json;

function select_neighborhood(ev, node_name) {
    ev.preventDefault();

    // Select all nodes in the neighborhood
    cy.nodes('[name = \'' + node_name + '\']').neighborhood().select();

    // Reset all nodes in the legend
    svg_legend.find(".legend_node").transform('scale', null);

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

                if (e.data('link_pcc') !== undefined) {
                    if (e.data('link_pcc') !== null) {
                        content.push({ value: 'Correlation (PCC): ' + e.data('link_pcc').toFixed(3) });
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

            // Fill data for legend
            var svg_families = [],
                svg_species = [];
            cy.nodes('[^compound]').forEach(function (n) {
                var family_color = n.data('family_color'),
                    family_shape = n.data('family_shape'),
                    family = n.data('family_name'),

                    species = n.data('species_name'),
                    species_color = n.data('species_color'),
                    species_shape = 'ellipse';

                if (species_color !== undefined) {
                    if (!svg_species.hasOwnProperty(species_color)) {
                        svg_species[species_color] = [];
                    }
                    svg_species[species_color][species_shape] = species;
                }

                if (family_color !== undefined) {
                    if (!svg_families.hasOwnProperty(family_color)) {
                        svg_families[family_color] = [];
                    }
                    svg_families[family_color][family_shape] = family;
                }

            }); //end cy.nodes.forEach

            if (Object.keys(svg_species).length > 0) { generate_legend(svg_species, 'species_color', 'species'); }

            $('.cy-node-color[attr="link_pcc"]').click();

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

    $('#cy-edge-score').on("slideStop", function (slideEvt) {
        var cutoff = slideEvt.value;

        cy.edges("[hrr>" + cutoff + "]").style('display', 'none');
        cy.edges("[hrr<=" + cutoff + "]").style('display', 'element');
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
                    if (node.data('gene_name').toLowerCase() === term ||
                            node.data('name').toLowerCase() === term ||
                            (node.data('family_name') !== null && node.data('family_name').toLowerCase() === term) ||
                            (node.data('interpro') !== undefined && node.data('interpro').indexOf(term.toUpperCase()) > -1) ||
                            valid_genes.indexOf(node.data('gene_id')) > -1 ||
                            (node.data('tokens') !== undefined && node.data('tokens') !== null && node.data('tokens').toLowerCase().includes(term))) {
                        node.toggleClass('found');
                    }
                });
            }
        }).done(function() {
            $('#search_logo').show();
            $('#search_spinner').hide();
        });
    });

    $('#cy-download-img-hires').click(function (ev) {
        ev.preventDefault();
        var png64 = cy.png({scale: 4, bg: "#FFFFFF"}),
            download = document.createElement('a');

        download.href = png64;
        download.download = 'cytoscape-hires.png';

        document.body.appendChild(download);
        download.click();
        document.body.removeChild(download);
    });

    $('#cy-download-img-lowres').click(function (ev) {
        ev.preventDefault();
        var png64 = cy.png({scale: 1, bg: "#FFFFFF"}),
            download = document.createElement('a');

        download.href = png64;
        download.download = 'cytoscape-lowres.png';

        document.body.appendChild(download);
        download.click();
        document.body.removeChild(download);
    });

    $('#cy-download-json').click(function (ev) {
        ev.preventDefault();
        var element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(initial_json));
        element.setAttribute('download', "cytoscape.json");

        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    });

    $('#cy-download-jsoncy').click(function (ev) {
        ev.preventDefault();
        var eles = cy.elements(),
            json = '',
            element = document.createElement('a');

        eles.each(function (i, ele) {
            if (ele.isNode()) {
                ele.data('current_color', ele.renderedStyle('background-color'));
                ele.data('current_shape', ele.renderedStyle('shape'));
            } else if (ele.isEdge()) {
                ele.data('current_color', ele.renderedStyle('line-color'));
                ele.data('current_width', ele.renderedStyle('width'));
            }
        });

        json = JSON.stringify(cy.json(), null, '\t');

        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(json));
        element.setAttribute('download', "cytoscape_full.json");

        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    });

    $('#cy-download-xgmml').click(function (ev) {
        ev.preventDefault();

        var xgmml = writeXGMML(cy),
            element = document.createElement('a');

        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(xgmml));
        element.setAttribute('download', "cytoscape.xgmml");

        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    });

    $('#cy-download-svg').click(function (ev) {
        ev.preventDefault();

        var svg = writeSVG(cy),
            element = document.createElement('a');

        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(svg));
        element.setAttribute('download', "cytoscape.svg");

        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    });

    $('#cy-download-svg-with-legend').click(function (ev) {
        ev.preventDefault();

        var svg_out = new Pablo(writeSVG(cy)),
            legend = new Pablo(svg_legend.markup(false)),
            graph_height = parseInt(Pablo.getAttributes(svg_out[0]).height.replace('px', ''), 10),
            graph_width = parseInt(Pablo.getAttributes(svg_out[0]).width.replace('px', ''), 10),
            legend_height = parseInt(Pablo.getAttributes(legend[0]).height.replace('px', ''), 10),
            legend_width = parseInt(Pablo.getAttributes(legend[0]).width.replace('px', ''), 10),
            total_height = graph_height + 20 + legend_height,
            total_width = (graph_width > legend_width ? graph_width : legend_width),
            l = svg_out.g({'id': 'legend'}).transform('translate', 0, graph_height + 20),
            element = document.createElement('a');

        l.append(legend);

        svg_out.attr('viewBox', '0 0 ' + total_width + ' ' + total_height);
        svg_out.attr('height', total_height + 'px');
        svg_out.attr('width', total_width + 'px');

        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(svg_out));
        element.setAttribute('download', "cytoscape_w_legend.svg");

        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    });

    $('#cy-download-png-with-legend').click(function (ev) {
        ev.preventDefault();

        var svg_out = new Pablo(writeSVG(cy)),
            legend = new Pablo(svg_legend.markup(false)),
            graph_height = parseInt(Pablo.getAttributes(svg_out[0]).height.replace('px', ''), 10),
            graph_width = parseInt(Pablo.getAttributes(svg_out[0]).width.replace('px', ''), 10),
            legend_height = parseInt(Pablo.getAttributes(legend[0]).height.replace('px', ''), 10),
            legend_width = parseInt(Pablo.getAttributes(legend[0]).width.replace('px', ''), 10),
            total_height = graph_height + 20 + legend_height,
            total_width = (graph_width > legend_width ? graph_width : legend_width),
            l = svg_out.g({'id': 'legend'}).transform('translate', 0, graph_height + 20);

        l.append(legend);

        svg_out.attr('viewBox', '0 0 ' + total_width + ' ' + total_height);
        svg_out.attr('height', total_height + 'px');
        svg_out.attr('width', total_width + 'px');

        svg_out.dataUrl('png', function (dataUrl) {
            var element = document.createElement('a');
            element.setAttribute('href', dataUrl);
            element.setAttribute('download', "cytoscape__w_legend.png");
            element.setAttribute('style', 'display:none');

            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
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