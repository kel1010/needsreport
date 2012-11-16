'use strict';

/* App Module */

angular.module('needsreport', []).
  config(['$routeProvider', function($routeProvider) {
  $routeProvider.
      when('', {templateUrl: 'partials/main.html', controller: main}).
      otherwise({redirectTo: ''});
}]);
