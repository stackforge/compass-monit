define(['./baseService'], function() {
    angular.module('compassMonitApp.services')
        .service('dataService', ['$http',
            function($http) {

                this.test = function() {
                    return $http.get("test");
                };
                this.graph = function(){
                	return $http.get("graph");
                };
                this.pieChart = function(){
                	return $http.get("pieChart");
                };

            }
        ]);
})