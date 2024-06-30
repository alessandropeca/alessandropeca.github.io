document.addEventListener("DOMContentLoaded", function() {
    const apiKey = 'Jqi8dLve7H7ixzmh0XQirKjB4miSf2Tnre3khV8y';  // Replace with your actual API key
    const apiUrl = 'https://api.adsabs.harvard.edu/v1/search/query?q=author:"Peca"&sort=date%20desc,bibcode%20desc';
    const proxyUrl = 'https://cors-anywhere.herokuapp.com/';

    fetch(proxyUrl + apiUrl, {
        headers: {
            'Authorization': `Bearer ${apiKey}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Log the data to the console to inspect the structure
        console.log(data);

        // Assuming data.response.docs contains the list of publications
        const publications = data.response.docs;
        const publicationsList = document.getElementById('publications-list');

        publications.forEach(publication => {
            const listItem = document.createElement('li');
            listItem.innerHTML = `
                <strong>Title:</strong> ${publication.title[0]}<br>
                <strong>Journal:</strong> ${publication.pub}, ${publication.pubdate}
            `;
            publicationsList.appendChild(listItem);
        });
    })
    .catch(error => console.error('Error fetching publications:', error));
});