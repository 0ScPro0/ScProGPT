const { createProxyMiddleware } = require('http-proxy-middleware');

// CRA dev-server proxy: forwards /api/* to the backend so the browser and
// the API share one origin (required for httpOnly SameSite=Lax cookies).
module.exports = function (app) {
    app.use(
        '/api',
        createProxyMiddleware({
            target: 'http://127.0.0.1:8000',
            changeOrigin: true,
        })
    );
};