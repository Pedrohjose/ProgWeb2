import './style.css'

const form = document.getElementById("form");
if (form) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = document.getElementById("btnSignIn");
    const email = document.getElementById("email").value;
    const senha = document.getElementById("password").value;
    let aviso = document.getElementById("login-feedback");
    if (!aviso) {
      aviso = document.createElement("p");
      aviso.id = "login-feedback";
      aviso.setAttribute("role", "alert");
      aviso.className = "text-sm text-red-300";
      form.append(aviso);
    }
    button.disabled = true;
    aviso.textContent = "Entrando...";
    try {
      const response = await fetch("http://40.127.11.169:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, senha }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Não foi possível entrar.");
      sessionStorage.setItem("estok.accessToken", data.access_token);
      sessionStorage.setItem("estok.refreshToken", data.refresh_token);
      sessionStorage.setItem("estok.perfil", data.usuario.perfil);
      window.location.replace("/home.html");
    } catch (error) {
      aviso.textContent = error instanceof TypeError
        ? "Não foi possível conectar à API. Verifique se o backend está ativo."
        : error.message;
    } finally {
      button.disabled = false;
    }
  });
}
