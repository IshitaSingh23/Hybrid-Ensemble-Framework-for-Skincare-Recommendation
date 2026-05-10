// Runtime deployment config for static hosts such as Vercel or Render.
// Local static servers should call the local FastAPI process.
(function () {
  var hostname = window.location && window.location.hostname;
  var isLocal =
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "::1" ||
    hostname === "";

  window.__UPSKIN_RUNTIME_CONFIG = window.__UPSKIN_RUNTIME_CONFIG || {
    apiUrl: isLocal ? "http://localhost:8000" : "https://upskin-api.onrender.com",
  };
})();
