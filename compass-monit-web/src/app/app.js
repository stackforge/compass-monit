define(['angular',
    'controllers',
    'directives',
    'services'
], function(ng) {

    'use strict';

    ng.module('compassMonitApp', ['compassMonitApp.controllers',
        'compassMonitApp.directives',
        'compassMonitApp.services'
    ])
});