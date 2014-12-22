define(['./baseService'], function() {
    angular.module('compassMonitApp.services')
        .factory('panelDataFactory', [
            function() {
                var panel = {};
                panel.init = function() {
                    this.draggableObjects = [];
                    this.enableFullScreen = false;
                    this.fullScreenURL = "src/app/partials/fullScreenContainer.html";
                    this.panelContainerURL = "src/app/partials/panel_container.html";
                    this.widthBase = 350;
                    // this.heightBase = 300;
                }
                panel.init();
                panel.getDraggableObjects = function() {
                    return this.draggableObjects;
                };
                panel.getEnableFullScreen = function() {
                    return this.enableFullScreen;
                }
                panel.getFullScreenURL = function() {
                    return this.fullScreenURL;
                };
                panel.getPanelContainer = function() {
                    return this.panelContainerURL;
                };
                panel.getWidth = function(index) {

                    return this.widthBase * panel.draggableObjects[index].widthFactor;
                };
                // panel.getHeight = function(index){

                //     return this.heightBase * panel.draggableObjects[index].widthFactor;
                // };

                return panel;
            }
        ]);
})