const ACCESS_KEY = "estok.accessToken";
const REFRESH_KEY = "estok.refreshToken";
let refreshInFlight = null;

function encerrarSessao() {
  sessionStorage.removeItem(ACCESS_KEY);
  sessionStorage.removeItem(REFRESH_KEY);
  sessionStorage.removeItem("estok.perfil");
  window.location.replace("/");
}

function renovarAccessToken() {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = renovarAccessTokenUnico();
  return refreshInFlight.finally(() => { refreshInFlight = null; });
}

async function renovarAccessTokenUnico() {
  const refreshToken = sessionStorage.getItem(REFRESH_KEY);
  if (!refreshToken) return false;
  const response = await fetch("/api/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) return false;
  const tokens = await response.json();
  sessionStorage.setItem(ACCESS_KEY, tokens.access_token);
  sessionStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  return true;
}

export async function apiFetch(path, options = {}) {
  const enviar = () => fetch(`/api${path}`, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${sessionStorage.getItem(ACCESS_KEY) || ""}`,
    },
  });
  let response = await enviar();
  if (response.status === 401 && await renovarAccessToken()) response = await enviar();
  if (response.status === 401) encerrarSessao();
  return response;
}

export async function logout() {
  const refreshToken = sessionStorage.getItem(REFRESH_KEY);
  if (refreshToken) {
    await fetch("/api/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    }).catch(() => {});
  }
  encerrarSessao();
}
