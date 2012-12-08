var opts = {
    zoom: 2,
    center: new google.maps.LatLng(20, 12),
    mapTypeId: google.maps.MapTypeId.ROADMAP
}
var map = new google.maps.Map(document.getElementById("map"), opts);

var clusters = [];
var styles = [];

var data;

function drawType(key) {
    var points = data[key];
    var markers = [];
    for (var i=0; i<points.length; ++i) {
        var point = points[i];
        var latLng = new google.maps.LatLng(point.loc[0], point.loc[1]);
           var marker = new google.maps.Marker({
               position: latLng,
               draggable: false,
               icon: markerImage
           });
           markers.push(marker);

         //var zoom = parseInt(document.getElementById('zoom').value, 10);
         //var size = parseInt(document.getElementById('size').value, 10);
         //var style = parseInt(document.getElementById('style').value, 10);
         //zoom = zoom == -1 ? null : zoom;
         //size = size == -1 ? null : size;
         //style = style == -1 ? null: style;
    }
    var cluster = new MarkerClusterer(map, markers, {
        maxZoom: null,
        gridSize: null,
        styles: styles[key]
    });
    clusters[key]=cluster;
}

function removeType(key) {
    clusters[key].clearMarkers();
}

$(document).ready(function () {
    $.getJSON('/a/group_data', function(res) {
        data = res['data'];
        var types = res['types'];

        for (var i=0; i<types.length; ++i) {
            var type = types[i];
            $("#legend").append("<input class='type' type='checkbox' checked='true' id='"+type+"'><img src='/static/images/"+type+".png'/>"+type+"<br/>");
        }

        $(".type").change(function() {
            var key = $(this).attr('id');
            if ($(this).attr('checked')) {
                drawType(key);
            } else {
                removeType(key);
            }
        });

        for (var key in data) {
            styles[key] = [];
            for (var t=35; t<=55; t+=10) {
                var url = "/static/images/"+key+t+".png";
                var s = {
                    url: url,
                    height: t,
                    width: t,
                }
                styles[key].push(s);
            }
            drawType(key);                    
        }
    });
});
