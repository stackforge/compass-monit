define(['./baseController'], function() {
    'use strict';

    angular.module('compassMonitApp.controllers')
        .controller('appController', function($scope, $modal, $log) {

            // $scope.draggableObjects = [{"title":"test","data":"[[0, 12], [7, 12], null, [7, 2.5], [12, 2.5]]"}];
            $scope.draggableObjects = [];


            $scope.onDropComplete = function(index, obj, evt) {
                var otherObj = $scope.draggableObjects[index];
                var otherIndex = $scope.draggableObjects.indexOf(obj);
                $scope.draggableObjects[index] = obj;
                $scope.draggableObjects[otherIndex] = otherObj;
            }

            $scope.panelContainers = "src/app/partials/panel_container.html";


            $scope.edit = function() {
                console.log("triggered")
            }

            /** ======== open chart config modal ========*/
            $scope.open = function() {
                var modalInstance = $modal.open({
                    templateUrl: 'src/app/partials/modal/modal_template.html',
                    controller: 'ChartConfigInstanceCtrl'
                });

                modalInstance.result.then(function(panel) {
                    //get data for specific panel
                    // panel.data=[];
                    // dataService.test().success(function(data){
                    //     panel.data = data;
                    // });
                    $scope.draggableObjects.push(panel);
                }, function() {
                    $log.info('Modal dismissed at: ' + new Date());
                });
            }

        });

});