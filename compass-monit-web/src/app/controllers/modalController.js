define(['./baseController'], function() {
    'use strict';

    angular.module('compassMonitApp.controllers')
        .controller('ChartConfigInstanceCtrl', function($scope, $modalInstance, dataService) {
            $scope.title = "Chart Config";
            $scope.chartTypes = ["graph", "gauge", "pie"];
            //$scope.content = "put inline content here";
            $scope.contentURL = "src/app/partials/modal/chart_config.html";
            $scope.panel = {};
            $scope.panel.chartType = "graph";
            $scope.ok = function() {
                dataService.test().success(function(data) {
                    $scope.panel.data = data;
                    $modalInstance.close($scope.panel);
                });
            };

            $scope.cancel = function() {
                $modalInstance.dismiss('cancel');
            };
        });

});