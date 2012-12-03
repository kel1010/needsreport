'use strict';

/* Controllers */

function main($scope, $http) {
	$http.get("/a/init_data").success(function(res) {
		$scope.CONTINENTS=['Africa', 'Asia', 'Australia', 'Europe', 'North America', 'South America'];
		$scope.CONTINENT_LOCATIONS={ // [lat, lng, zoom_level]
			'Africa': [7.19, 21.10, 3],
			'Asia': [29.84, 89.30, 3],
			'Australia': [-27.00, 133.0, 4],
			'Europe': [48.69, 9.14, 4],
			'North America': [46.07, -100.55, 3],
			'South America': [-14.60, -57.66, 3]
		};
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
		$scope.last_continent = null;
		$scope.TYPES=res['types'];

		$scope.infoWin = new google.maps.InfoWindow({
			size: new google.maps.Size(350, 350)
   		});

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
		var opts = {
			zoom: 2,
			center: new google.maps.LatLng(20, 12),
			mapTypeId: google.maps.MapTypeId.ROADMAP
		}
		$scope.map = new google.maps.Map(document.getElementById("map"), opts);
		$scope.markers = Array();

		var countyLayer = new google.maps.FusionTablesLayer({
			query: {
				select: 'geometry',
				from: '0IMZAFCwR-t7jZnVzaW9udGFibGVzOjIxMDIxNw'
			},
		});

		//countyLayer.setMap($scope.map);

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
		       		map: $scope.map
		       	});
		       	marker.point = point;
		       	$scope._createMarkerListener(marker, start, end);
		       	if (type in $scope.markers) {
		       		$scope.markers[type].push(marker);
				} else {
					$scope.markers[type] = [marker];
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

	$scope.selectContinent = function() {
		if ($scope.last_continent!=$scope.selected.continent) {
			var loc = $scope.CONTINENT_LOCATIONS[$scope.selected.continent];
			var latLng = new google.maps.LatLng(loc[0], loc[1]);
			$scope.map.setCenter(latLng);
			$scope.map.setZoom(loc[2]);
			$scope.last_continent=$scope.selected.continent;
		} else {
			$scope.last_continent=$scope.selected.continent=null;
			$scope.map.setCenter(new google.maps.LatLng(20, 12));
			$scope.map.setZoom(2);
		}
	}

}

