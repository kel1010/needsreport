'use strict';

/* App Module */

angular.module('needsreport', []).
  config(['$routeProvider', function($routeProvider) {
  $routeProvider.
      when('', {templateUrl: STATIC_URL+'partials/main.html', controller: main}).
      otherwise({redirectTo: ''});
}]);
