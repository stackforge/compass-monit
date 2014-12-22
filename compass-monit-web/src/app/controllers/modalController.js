define(['./baseController'], function() {
    'use strict';

    angular.module('compassMonitApp.controllers')
        .controller('ChartConfigInstanceCtrl', function($scope, $modalInstance, dataService, selected, panelDataFactory) {
            /*when selected == null, it is to create a new chart; when selected != null, it is to modify a selected chart" */
             
            $scope.selected = selected;
            $scope.title = "Chart Config";
            $scope.chartTypes = ["graph", "gauge", "pie"];
            $scope.panelWidthOptions = [1, 1.5, 2, 2.5, 3, 3.5];
            //$scope.content = "put inline content here";
            $scope.contentURL = "src/app/partials/modal/chart_config.html";
            if (selected == null) {
                $scope.panel = {};
                $scope.panel.chartType = "graph";
                $scope.panel.widthFactor = 1;
            }else{
                $scope.panel = angular.copy(panelDataFactory.draggableObjects[selected]);
            }

            $scope.ok = function() {
                if(selected == null)
                {
                    if ($scope.panel.chartType == "graph") {
                        dataService.graph().success(function(data) {
                            $scope.panel.data = data;
                            $modalInstance.close($scope.panel);
                        });
                    } else if ($scope.panel.chartType == "pie") {
                        dataService.pieChart().success(function(data) {
                            $scope.panel.data = data;
                            $modalInstance.close($scope.panel);
                        });
                    }
                }
                else{
                    panelDataFactory.draggableObjects[selected] = angular.copy($scope.panel);
                    $modalInstance.close(null);
                }
                

            };

            $scope.cancel = function() {
                $modalInstance.dismiss('cancel');
            };
        });

});