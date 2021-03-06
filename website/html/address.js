function initialize() {
    var address = (document.getElementById('my-address'));
    var autocomplete = new google.maps.places.Autocomplete(address);
    autocomplete.setTypes(['geocode']);
    google.maps.event.addListener(autocomplete, 'place_changed', function() {
        var place = autocomplete.getPlace();
            if (!place.geometry) {
                return;
            }

        var address = '';
        if (place.address_components) {
            address = [
                (place.address_components[0] && place.address_components[0].short_name || ''),
                (place.address_components[1] && place.address_components[1].short_name || ''),
                (place.address_components[2] && place.address_components[2].short_name || '')
                ].join(' ');
        }
      });
}
function codeAddress() {
    geocoder = new google.maps.Geocoder();
    var address = document.getElementById("my-address").value;
    localStorage.setItem("address",address)
    geocoder.geocode( { 'address': address}, function(results, status) {
      if (status == google.maps.GeocoderStatus.OK) {
        localStorage.setItem("latitude",results[0].geometry.location.lat())
        localStorage.setItem("longitude",results[0].geometry.location.lng())

    // document.getElementById("latitude").value= ("Latitude: "+results[0].geometry.location.lat());
    // document.getElementById("longitude").value=("Longitude: "+results[0].geometry.location.lng());
    //alert("Longitude: "+results[0].geometry.location.lng())
    
      } 

      else {
        alert("Geocode was not successful for the following reason: " + status);
      }
    });
    var iframe = $("#forPostyouradd");
    iframe.attr("src", iframe.data("src")); 
  }
google.maps.event.addDomListener(window, 'load', initialize);

       