define(['./baseService'], function() {
    angular.module('compassMonitApp.services')
        .service('dataService', ['$http',
            function($http) {

                this.test = function() {
                    return $http.get("test");
                };

            }
        ]);
})