const express = require('express');
const request = require('request');
const app = express();
const PORT = 3000;

app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

app.get('/ads', (req, res) => {
    const url = 'https://api.adsabs.harvard.edu/v1/search/query';
    const token = 'Jqi8dLve7H7ixzmh0XQirKjB4miSf2Tnre3khV8y';  // Replace with your actual token

    request.get({
        url: url,
        qs: req.query,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    }, (error, response, body) => {
        if (error) {
            return res.status(500).send(error);
        }
        res.send(body);
    });
});

app.listen(PORT, () => {
    console.log(`Proxy server running at http://localhost:${PORT}`);
});
