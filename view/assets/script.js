window.onload = () => {
    let places = staticLoadPlaces();
    renderPlaces(places);
};

function staticLoadPlaces() {
   return [
       {
           name: 'map_pointer',
           location: {
               lat: 50.6298328,
               lng: 4.8629798,
           }
       },
   ];
}

function renderPlaces(places) {
   let scene = document.querySelector('a-scene');

    places.forEach((place) => {
        let latitude = place.location.lat;
        let longitude = place.location.lng;
        
        let model = document.createElement('a-entity');
        model.setAttribute('gps-entity-place', `latitude: ${latitude}; longitude: ${longitude};`);
        model.setAttribute('gltf-model', 'map_pointer/scene.gltf');
        model.setAttribute('scale', '1 5 1');
        
        model.addEventListener('mouseenter', function () {
            model.setAttribute('scale', '1 2 1')
            console.log('click')
        })

        model.addEventListener('mouseleave', function () {
            model.setAttribute('scale', '1 5 1')
            console.log('click')
        })

        model.addEventListener('loaded', () => {
            window.dispatchEvent(new CustomEvent('gps-entity-place-loaded'))
        });

        scene.appendChild(model);

    },(err) => {
        console.log(err)
    });
}