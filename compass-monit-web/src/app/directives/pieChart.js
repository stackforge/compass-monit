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

                var placeHolder = '<div id="placeholder_' + scope.graphIndex + '" class="demo-placeholder"></div>';
                element.append(placeHolder);

                $.plot("#placeholder_" + scope.graphIndex, scope.graphData, {
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