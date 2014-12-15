define(['./baseController'], function() {
    'use strict';

    angular.module('compassMonitApp.controllers')
        .controller('monitAppController', function($scope, $modal, $log) {

            // $scope.draggableObjects = [{"title":"test","data":"[[0, 12], [7, 12], null, [7, 2.5], [12, 2.5]]"}];
            $scope.draggableObjects = [];
            $scope.enableFullScreen = false;
            $scope.fullScreenURL= "src/app/partials/fullScreenContainer.html";

            $scope.onDropComplete = function(index, obj, evt) {
                var otherObj = $scope.draggableObjects[index];
                var otherIndex = $scope.draggableObjects.indexOf(obj);
                $scope.draggableObjects[index] = obj;
                $scope.draggableObjects[otherIndex] = otherObj;
            }

            $scope.panelContainers = "src/app/partials/panel_container.html";


            $scope.edit = function() {
                console.log("triggered")
            };

            $scope.fullScreen = function(index){
                $scope.enableFullScreen = true;
                $scope.fullScreenObject = $scope.draggableObjects[index];
            };

            $scope.closeFullScreen = function(){
                $scope.enableFullScreen = false;
                $scope.fullScreenObject = {};
            };
            $scope.removePanel = function(index){
                $scope.draggableObjects.splice(index,1);
            };

            /** ======== open chart config modal ========*/
            $scope.open = function() {
                var modalInstance = $modal.open({
                    templateUrl: 'src/app/partials/modal/modal_template.html',
                    controller: 'ChartConfigInstanceCtrl'
                });

                modalInstance.result.then(function(panel) {
                    $scope.draggableObjects.push(panel);
                }, function() {
                    $log.info('Modal dismissed at: ' + new Date());
                });
            }

        });

});