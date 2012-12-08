'use strict';

/* Controllers */

function main($scope, $http) {
    $http.get("/a/init_data").success(function(res) {
        $scope.CONTINENTS=['Africa', 'Asia', 'Australia', 'Europe', 'North America', 'South America'];
        $scope.TYPE_COLOR = {
            'Education': '#f06697',
            'Health': '#ed2224',
            'Sanitation': '#5e53a3',
            'Employment': '#f26822',
            'Water': '#1195cb',
            'Agriculture': '#a1cd3a',
            'Infrastructure': '#ebea62',
            'Corruption': '#000'
        };
        $scope.TYPES=res['types'];
        $scope.CONTINENTS=res['continents'];
        $scope.map=null;

        $scope.infoWin = new google.maps.InfoWindow({
            size: new google.maps.Size(350, 350)
           });
        
        $scope.LAYERS = [
            {
                name: 'US County',
                layer: new google.maps.FusionTablesLayer({
                    query: {
                        select: 'geometry',
                        from: '0IMZAFCwR-t7jZnVzaW9udGFibGVzOjIxMDIxNw'
                    }
                })
            },
            {
                name: 'World Population Growth Rate',
                layer: new google.maps.FusionTablesLayer({
                    query: {
                        select: 'geometry, Name, Rate',
                        from: '1osw8Yiy-zDS2P4_-GoIy8d11KvW6qYqiac2_6LY'
                    }
                })
            },
            {
                name: 'World Life Expectancy',
                layer: new google.maps.FusionTablesLayer({
                    query: {
                        select: 'geometry, Name, Rate',
                        from: '1gB6YRzBDrNqfhs8wAsNhGkC_vI4LczSms72oqBU'
                    }
                })
            }
        ];

        $scope._initTimeline(res['min_time']);
    });

    $scope._initTimeline = function(min_time) {

        var timeline = new google.visualization.AnnotatedTimeLine(document.getElementById("timeline"));

        var end = new Date().getTime();
        var start = end - 7889000000;

        var data = new google.visualization.DataTable();
        data.addColumn('date', 'Date');
        data.addColumn('number', 'count');
        data.addRows([
            [new Date(min_time*1000), 0],
            [new Date(), 0]
        ]);
        timeline.draw(data, {
            displayAnnotations: false,
        });

        timeline.setVisibleChartRange(new Date(start), new Date(end));

        google.visualization.events.addListener(timeline, 'rangechange', function() {
            var range = timeline.getVisibleChartRange();
            var start = range.start.getTime();
            var end = range.end.getTime();
            $http.post("/a/map_data", {start: start/1000, end: end/1000}).success(function(res) {
                $scope.data = res['data'];
                $scope._drawMap(start, end);
            });
        });

        $http.post("/a/map_data", {start: start/1000, end: end/1000}).success(function(res) {
            $scope.data = res['data'];
            $scope._drawMap(start, end);
        });

    }

    $scope._createMarkerListener = function(marker, start, end) {

           google.maps.event.addListener(marker, 'click', function(e) {
               $http.post("/a/loc_data", {loc_place:marker.point.loc_place, start:start/1000, end:end/1000}).success(function(res) {
                   $scope.infoWin.close();
                   var chartDiv = document.createElement("div");
                   var chart = new google.visualization.BarChart(chartDiv);
                   var data = Array();
                   data[0] = Array();
                   data[0][0] = 'Category';
                   var colors = [];
                   for (var i=0; i<res.length; ++i) {
                       data[i+1] = Array();
                       data[i+1][0]=res[i].type;
                       data[0][i+1]='';
                       var color = $scope.TYPE_COLOR[res[i].type];
                       colors[i] = color;
                   }
                   for (var i=0; i<res.length; ++i) {
                       for (var j=0; j<res.length; ++j) {
                           if (i==j) {
                               data[i+1][j+1] = res[i].sum;
                           } else {
                               data[i+1][j+1] = 0;
                           }
                       }
                   }
                   chart.draw(google.visualization.arrayToDataTable(data), {
                       width: 300,
                       height: 200,
                       legend: {position: 'none'},
                       isStacked: true,
                       colors: colors,
                       title: 'Needs for '+marker.point.loc_place
                   });
                   $scope.infoWin.setContent(chartDiv);
                   $scope.infoWin.open(marker.get('map'), marker);
               });
           });
    }
    
    $scope._drawMap = function(start, end) {
        if ($scope.map==null) {
            var opts = {
                zoom: 2,
                center: new google.maps.LatLng(20, 12),
                mapTypeId: google.maps.MapTypeId.ROADMAP
            }
            $scope.map = new google.maps.Map(document.getElementById("map"), opts);
        } else {
            for (var i=0; i<$scope.TYPES.length; ++i) {
                var type = $scope.TYPES[i];
                for (var j=0; j<$scope.markers[type].length; ++j) {
                    $scope.markers[type][j].setMap(null);
                }
            }
        }
        $scope.markers = Array();
        for (var i=0; i<$scope.TYPES.length; ++i) {
            var type = $scope.TYPES[i];
            $scope.markers[type] = Array();
        }
        if ($scope.stypes[type]) {
        }
        for (var i=0; i<$scope.data.length; ++i) {
            var point = $scope.data[i];
            if (point.loc) {
            	var type = point.type;
                var url = "images/"+type+($scope.data[i].value)+".png";
                var latLng = new google.maps.LatLng(point.loc[0], point.loc[1]);            
                var marker = new google.maps.Marker({
					position: latLng,
					draggable: false,
					icon: url,
					clickable: true,
                 });
                 marker.point = point;
                 $scope._createMarkerListener(marker, start, end);
                 if (type in $scope.markers) {
                       $scope.markers[type].push(marker);
                 } else {
                	 	$scope.markers[type] = [marker];
                 }
                 if ($scope.stypes[type]) {
 					marker.setMap($scope.map);
                 }
            }
        }
        
    }

    $scope.changeTypes = function(type) {
        for (var i=0; i<$scope.markers[type].length; ++i) {
            if ($scope.stypes[type]) {
                $scope.markers[type][i].setMap($scope.map);
            } else {
                $scope.markers[type][i].setMap(null);
            }
        }
    }

    $scope.selectContinent = function(continent) {
        if ($scope.selectedContinent!=continent) {
            var latLng = new google.maps.LatLng(continent['latlng'][0], continent['latlng'][1]);
            $scope.map.setCenter(latLng);
            $scope.map.setZoom(continent['zoom']);
            $scope.selectedContinent=continent;
        } else {
            $scope.selectedContinent=null;
            $scope.map.setCenter(new google.maps.LatLng(20, 12));
            $scope.map.setZoom(2);
        }
    }

    $scope.selectCountry = function(country) {
        if ($scope.selectedCountry!=country) {
            var latLng = new google.maps.LatLng(country['latlng'][0], country['latlng'][1]);
            $scope.map.setCenter(latLng);
            $scope.map.setZoom(country['zoom']);
            $scope.selectedCountry=country;
        }
    }

    $scope.selectLayer = function(layer) {
        if ($scope.selectedLayer!=null) {
            $scope.selectedLayer.layer.setMap(null);
        }
        if ($scope.selectedLayer==layer) {
        	$scope.selectedLayer = null;
        } else {
	        layer.layer.setMap($scope.map);
	        $scope.selectedLayer = layer;
        }
    }

}
