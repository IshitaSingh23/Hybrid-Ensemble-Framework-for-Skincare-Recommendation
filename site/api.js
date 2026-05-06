// Up Skin API client — single source of truth for backend calls.
// Base URL pattern matches the handoff brief (NEXT_PUBLIC_UPSKIN_API_URL).
// In a Next/Vite app this would read from import.meta.env or process.env;
// here it falls back through a runtime override + localhost.

(function () {
  function queryApiBase() {
    if (typeof window === "undefined") return "";
    const params = new URLSearchParams(window.location.search);
    return params.get("api") || "";
  }

  const RUNTIME_BASE =
    (typeof window !== "undefined" && window.__UPSKIN_API_URL) ||
    (typeof window !== "undefined" &&
      window.__UPSKIN_RUNTIME_CONFIG &&
      window.__UPSKIN_RUNTIME_CONFIG.apiUrl) ||
    (typeof process !== "undefined" && process.env && process.env.NEXT_PUBLIC_UPSKIN_API_URL) ||
    queryApiBase() ||
    "http://localhost:8000";

  // Real FastAPI mode is the default. Opt into the offline mock layer by
  // setting `window.__UPSKIN_USE_MOCK = true` *before* this script loads
  // (see index.html for an example). The mock is only intended for design
  // preview when no backend is reachable; the production flow always hits
  // the FastAPI service.
  const USE_MOCK = typeof window !== "undefined" && window.__UPSKIN_USE_MOCK === true;

  async function request(path, opts = {}) {
    if (USE_MOCK && window.mockApi) return mockRoute(path, opts);

    let res;
    try {
      res = await fetch(RUNTIME_BASE + path, {
        headers: { "Content-Type": "application/json" },
        ...opts,
      });
    } catch (networkErr) {
      const err = new Error("Could not reach the recommender service.");
      err.status = 0;
      err.detail = networkErr && networkErr.message
        ? networkErr.message
        : "The backend is unreachable. Make sure FastAPI is running on " + RUNTIME_BASE + ".";
      throw err;
    }

    if (!res.ok) {
      let detail = "";
      try {
        const data = await res.json();
        detail = (data && (data.detail || data.message)) || JSON.stringify(data);
      } catch (_jsonErr) {
        detail = await res.text().catch(() => "");
      }
      const err = new Error("Request failed (" + res.status + ")");
      err.status = res.status;
      err.detail = detail;
      throw err;
    }
    return res.json();
  }

  function mockRoute(path, opts) {
    return new Promise((resolve, reject) => {
      const delay = 280 + Math.random() * 320;
      setTimeout(() => {
        try {
          if (path === "/health") return resolve(window.mockApi.health());
          if (path === "/model/metrics") return resolve(
            window.mockApi.metrics ? window.mockApi.metrics() : window.mockApi.health()
          );
          if (path.startsWith("/demo-users")) return resolve(window.mockApi.demoUsers());
          if (path.startsWith("/products/search")) {
            const q = new URL("http://x" + path).searchParams.get("q") || "";
            return resolve(window.mockApi.search(q));
          }
          if (path.startsWith("/recommendations/") && opts.method !== "POST") {
            const id = path.split("/")[2].split("?")[0];
            return resolve(window.mockApi.recommendForUser(id, 10));
          }
          if (path === "/recommendations/custom" && opts.method === "POST") {
            return resolve(window.mockApi.recommendCustom(JSON.parse(opts.body)));
          }
          reject(new Error("unknown route " + path));
        } catch (e) { reject(e); }
      }, delay);
    });
  }

  window.upskinApi = {
    baseUrl: RUNTIME_BASE,
    usingMock: USE_MOCK,
    health: () => request("/health"),
    metrics: () => request("/model/metrics"),
    demoUsers: (limit = 25) => request("/demo-users?limit=" + limit),
    searchProducts: (q, limit = 20) =>
      request("/products/search?q=" + encodeURIComponent(q || "") + "&limit=" + limit),
    recommendForUser: (id, top_n = 10) =>
      request("/recommendations/" + encodeURIComponent(id) + "?top_n=" + top_n),
    recommendCustom: (payload) =>
      request("/recommendations/custom", { method: "POST", body: JSON.stringify(payload) }),
  };
})();
