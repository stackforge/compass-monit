define(['./baseDirective'], function() {
    angular.module('compassMonitApp.directives')
        .directive('graph', function() {
        return {
            restrict: 'E',
            scope: {
                graphData: "=",
                graphIndex: "@",
                fullScreen: "@"
            },
            link: function(scope, element, attrs) {
                console.log("panelWidth",scope.width)
                var placeHolder = '<div id="placeholder_' + scope.graphIndex + '" class="demo-placeholder"></div>';
                element.append(placeHolder);
                
                var options = {
                    xaxis: {
                        mode: "time",
                        tickLength: 5
                    },
                    selection: {
                        mode: "x"
                    }
                };
                if(scope.fullScreen == "true")
                {
                    var overview = '<div id="overview_' + scope.graphIndex + '" class="demo-placeholder" style="height:150px"></div>';
                    element.append(overview);

                    var overview = $.plot("#overview_" + scope.graphIndex, scope.graphData, {
                        series: {
                            lines: {
                                show: true,
                                lineWidth: 1
                            },
                            shadowSize: 0
                        },
                        xaxis: {
                            ticks: [],
                            mode: "time"
                        },
                        yaxis: {
                            ticks: [],
                            min: 0,
                            autoscaleMargin: 0.1
                        },
                        selection: {
                            mode: "x"
                        }
                    });
                }

                var plot = $.plot("#placeholder_" + scope.graphIndex, scope.graphData, options);
                $("#placeholder_" + scope.graphIndex).bind("plotselected", function (event, ranges) {

                    // do the zooming
                    $.each(plot.getXAxes(), function(_, axis) {
                        var opts = axis.options;
                        opts.min = ranges.xaxis.from;
                        opts.max = ranges.xaxis.to;
                    });
                    plot.setupGrid();
                    plot.draw();
                    plot.clearSelection();

                    // don't fire event on the overview to prevent eternal loop
                    if(scope.fullScreen == "true")
                    {
                         overview.setSelection(ranges, true);
                    }
                });
                if(scope.fullScreen == "true")
                {
                    $("#overview_" + scope.graphIndex).bind("plotselected", function (event, ranges) {
                        plot.setSelection(ranges);
                    });
                }
            }
        }
    });
});