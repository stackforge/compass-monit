define(['./baseDirective'], function() {
    angular.module('compassMonitApp.directives')
        .directive('pieChart', function() {
            return {
                restrict: 'E',
                scope: {
                    graphData: "=",
                    graphIndex: "@"
                },
                link: function(scope, element, attrs) {
                    var id = (new Date()).getTime();
                    var placeHolder = '<div id="placeholder_' + id + '" class="demo-placeholder"></div>';
                    element.append(placeHolder);

                    $.plot("#placeholder_" + id, scope.graphData, {
                        series: {
                            pie: {
                                show: true
                            }
                        }
                    });
                }
            }
        });
});