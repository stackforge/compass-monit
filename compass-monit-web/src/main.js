require.config({
    baseUrl: "src",
    paths: {
        'jquery': '../vendor/jquery/jquery-1.11.1.min',
        'jqueryUI':'../vendor/jquery/jquery-ui-1.10.3',
        'flot': '../vendor/jquery/jquery.flot',
        'flotSelection': '../vendor/jquery/jquery.flot.selection',
        'flotTime': '../vendor/jquery/jquery.flot.time',
        'flotPie': '../vendor/jquery/jquery.flot.pie',
        'flotResize': '../vendor/jquery/jquery.flot.resize',
        'angular': '../vendor/angular/angular.min',
        'ngMocks': '../vendor/angular/angular-mocks',
        'uiBootstrap': '../vendor/angular_bootstrap/ui-bootstrap-tpls-0.12.0.min',
        'ngDraggable': '../vendor/angular/ngDraggable',

        'controllers':'app/controllers/allControllers',
        'directives':'app/directives/allDirectives',
        'services':'app/services/allServices'
    },
    shim: {
        "jquery": {
            exports: "jquery"
        },
        "jqueryUI":{
            deps:["jquery"],
            exports: "jqueryUI"
        },
        "flot":{
            deps:["jquery"],
            exports: "flot"
        },
        "flotSelection":{
            deps:["flot"],
            exports:'flotSelection'
        },
        "flotPie":{
            deps:["flot"],
            exports:'flotPie'
        },
        "flotResize":{
            deps:["flot"],
            exports:'flotResize'
        },
        "flotTime":{
            deps:["flot"],
            exports:'flotTime'
        },
        "angular": {
            deps: ['jquery'],
            exports: "angular"
        },
        "ngMocks":{
            deps:['angular'],
            exports:"ngMocks"
        },
        "uiBootstrap":{
            deps: ['angular'],
            exports: "uiBootstrap"
        },
        "ngDraggable":{
            deps: ['angular'],
            exports: "ngDraggable"
        }
    },

    deps: ['./bootstrap']
});
