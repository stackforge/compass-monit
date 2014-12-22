define(['./baseController'], function() {
    'use strict';

    angular.module('compassMonitApp.controllers')
        .controller('monitAppController', function($scope, $modal, $log, $http, panelDataFactory) {

            // $scope.draggableObjects = [{"title":"test","data":"[[0, 12], [7, 12], null, [7, 2.5], [12, 2.5]]"}];
            $scope.draggableObjects = panelDataFactory.getDraggableObjects();
            window.foo = $scope.draggableObjects;
            window.foo1 = panelDataFactory.getDraggableObjects();
            $scope.enableFullScreen = panelDataFactory.getEnableFullScreen();
            $scope.fullScreenURL= panelDataFactory.getFullScreenURL();

            $http.get("src/app/dashboardConfig/dashboardConfig.json").success(function(preConfig){
                angular.forEach(preConfig,function(obj){
                    $scope.draggableObjects.push(obj);
                });
                // $scope.draggableObjects = angular.fromJson(preConfig);
                // console.log($scope.draggableObjects)

            });

            $scope.onDropComplete = function(index, obj, evt) {
                var otherObj = $scope.draggableObjects[index];
                var otherIndex = $scope.draggableObjects.indexOf(obj);
                $scope.draggableObjects[index] = obj;
                $scope.draggableObjects[otherIndex] = otherObj;
            }

            $scope.panelContainers = panelDataFactory.getPanelContainer();

            $scope.fullScreen = function(index){
                console.log(index)
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

            $scope.getPanelWidth = function(index){
                return panelDataFactory.getWidth(index);
            };

            /** ======== open chart config modal ========*/
            $scope.open = function(index) {
                var modalInstance = $modal.open({
                    templateUrl: 'src/app/partials/modal/modal_template.html',
                    controller: 'ChartConfigInstanceCtrl',
                    resolve:{
                        selected: function(){
                            return index;
                        }
                    }
                });
                    
                modalInstance.result.then(function(panel) {
                    if(panel != null){
                        $scope.draggableObjects.push(panel);
                    }
                    
                }, function() {
                    $log.info('Modal dismissed at: ' + new Date());
                });
            }

        });

});