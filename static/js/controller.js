'use strict';

/* Controllers */

function main($scope, $http) {
    $http.put("/a/init_data").success(function(res) {
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
        $scope.stypes = Array();

    	$scope.STATIC_URL = STATIC_URL;        

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

        $scope._initTimeline(res['min_time'], res['chart_data']);

        document.getElementById('loading').style.visibility='hidden';        
    });

    $scope.$on('$viewContentLoaded', function(event) {
        window._gaq.push(['_trackPageview', window.location.path]);
    });

    $scope._initTimeline = function(min_time, chart_data) {
    	$scope.timeline = new Highcharts.StockChart({
            chart: {
                renderTo: 'timeline',
                alignTicks: false,
    			type: "column",
                events: {
                	redraw: function() {
                		$scope.load();
                	}
                }    	
            },
            xAxis: {
            	tickWidth: 0,
            	tickLength: 0,
            	tickPosition: 'inside',
                labels: {enabled: false}
            },
            yAxis: {
                labels: {enabled: false}
            },            
            rangeSelector: {
                selected: 0
            },
            series: [{
                name: 'Needs',
                data: chart_data,
            }]
    	});

    	$scope._loadData($scope.timeline.xAxis[0].min, $scope.timeline.xAxis[0].max);

    }

    $scope._drawChart = function(marker) {
    	var start = $scope.timeline.xAxis[0].min;
    	var end = $scope.timeline.xAxis[0].max;
		$http.post("/a/loc_data", {loc_place:marker.point.loc_place, start:start/1000, end:end/1000}).success(function(res) {    	
            $scope.infoWin.close();
            var chartDiv = document.createElement("div");
            chartDiv.class = "chart";
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
            $scope.infoWin.open($scope.map, marker);
		});
    }  
    
    $scope._drawMap = function(start, end) {
        if ($scope.map==null) {
        	var animation = google.maps.Animation.DROP;
            var opts = {
                zoom: 2,
                center: new google.maps.LatLng(20, 12),
                mapTypeId: google.maps.MapTypeId.ROADMAP,
                overviewMapControl: true,
                overviewMapControlOptions: {opened: true},
                mapTypeControl: false,
                streetViewControl: false
                //panControlOptions: { position: google.maps.ControlPosition.RIGHT_CENTER },
                //zoomControlOptions: { position: google.maps.ControlPosition.RIGHT_CENTER }
            }
            $scope.map = new google.maps.Map(document.getElementById("map"), opts);
        } else {
        	var animation = google.maps.Animation.None;
        	for (var type in $scope.clusters) {
        		$scope.clusters[type].clearMarkers();
        	}
        }
        $scope.clusters = new Array();
        $scope._createMarkers();
    }

    $scope._createMarkerListener = function(marker) {
    	google.maps.event.addListener(marker, 'click', function(e) {
    		$scope._drawChart(marker);
    	});
    }
    
    $scope._createMarker = function(point) {
        if (point.loc) {
        	var type = point.type;
            var icon_url = STATIC_URL+"images/"+type+(point.value)+".png";
            var latLng = new google.maps.LatLng(point.loc[0], point.loc[1]);            
            var marker = new google.maps.Marker({
				position: latLng,
				draggable: false,
				icon: icon_url,
				clickable: true,
				title: type,
            });
            marker.sum = point.sum;

            marker.point = point;
            $scope._createMarkerListener(marker);
            return marker;
        }
    }

    $scope._createMarkers = function() {
        for (var type in $scope.data) {
        	var markers = new Array();
        	for (var j=0; j<$scope.data[type].length; ++j) {
        		var point = $scope.data[type][j];
        		markers.push($scope._createMarker(point));
        	}
        	$scope.clusters[type] = new MarkerClusterer($scope.map, markers, {
        		imagePath: $scope.STATIC_URL+"images/"+type,
        		imageExtension: 'png',
        		imageSizes: [20,25,30,35,40,40,45,50,55,60],
        		calculator: _markerClustererCalculator,
        		title: type,
        		minimumClusterSize: 1
        	});
        }
    }

    $scope.load = function() {
        $scope._loadData($scope.timeline.xAxis[0].min, $scope.timeline.xAxis[0].max);
    }

    $scope._loadData = function(start, end) {
    	var types = Array()
    	for(var type in $scope.stypes) {
    		if ($scope.stypes[type]) {
    			 types.push(type);
    		}
    	}

        window.setTimeout(document.getElementById('loading').style.visibility='visible', 500)        
	    $http.post("/a/map_data", {start: start/1000, end: end/1000, types: types}).success(function(res) {
	        $scope.data = res['data'];
	        $scope._drawMap(start, end);
	        document.getElementById('loading').style.visibility='hidden';
	    });
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

    $scope.showControls = function() {
    	var mapDiv = document.getElementById("left");
    	$scope.controlsLeft += 10;
    	if ($scope.controlsLeft>=0) {
    		$scope.$apply($scope.controlsLeft=0);
        	mapDiv.style.left = $scope.controlsLeft+"px";
    	} else {
        	mapDiv.style.left = $scope.controlsLeft+"px";
        	window.setTimeout($scope.showControls, 5);
    	}
    }

    $scope.hideControls = function() {
    	var mapDiv = document.getElementById("left");
    	$scope.controlsLeft -= 20;
    	if ($scope.controlsLeft<=-250) {
    		$scope.$apply($scope.controlsLeft=-250);
        	mapDiv.style.left = $scope.controlsLeft+"px";
    	} else {
        	mapDiv.style.left = $scope.controlsLeft+"px";
        	window.setTimeout($scope.hideControls, 5);
    	}
    }
    
}

function _markerClustererCalculator(markers, numStyles) {
	  var sum = 0;

	  for (var i=0; i<markers.length; ++i) {
		  sum+=markers[i].sum;
	  }

	  var index = Math.floor(Math.log(sum)/2.303)+1; // convert to base 10 log		  
	  if (markers.length==1) {
		  index = Math.min(index, 5);
	  } else {
		  index = Math.min(index, 5) + 5;
	  }

	  return {
		  text: sum+'',
		  index: index
	  };
}

