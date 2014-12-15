define(['ngMocks'], function() {
    var compassAppDev = angular.module('compassMonitApp.test', ['ngMockE2E']);

    compassAppDev.run(function($httpBackend, $http) {
        var progressPercent = 0;
        // Allow all calls not to the API to pass through normally
        $httpBackend.whenGET(new RegExp('src\/.*')).passThrough();
        $httpBackend.whenGET(new RegExp('data\/.*')).passThrough();
        //$httpBackend.whenGET(new RegExp('.*moni.*')).passThrough();

        $httpBackend.whenGET('test').respond(function(method, url, data) {
            console.log(method, url, data);
            var data = [
                        [0, 12],
                        [7, 12], null, [7, 2.5],
                        [12, 2.5]
                    ];
            return [200, data, {}];
        });

    });
});