define(['./baseService'], function() {
    angular.module('compassMonitApp.services')
        .service('dataService', ['$http',
            function($http) {

                this.test = function(user) {
                    return $http.get("test");
                };

            }
        ]);
})