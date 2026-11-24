import './style.css'
import { API_VM, cadastrar } from './listagens-api.js';

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
      const response = await fetch(`${API_VM}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, senha }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Não foi possível entrar.");
      sessionStorage.setItem("estok.accessToken", data.access_token);
      sessionStorage.setItem("estok.refreshToken", data.refresh_token);
      sessionStorage.setItem("estok.perfil", data.usuario.perfil);
      sessionStorage.setItem("estok.usuario", JSON.stringify({
        id: data.usuario.id, nome: data.usuario.nome,
        email: data.usuario.email, perfil: data.usuario.perfil,
      }));
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

const formForgotPassword = document.getElementById("formForgotPassword");

if (document.getElementById('sessao-nome')) {
  let usuario;
  try { usuario = JSON.parse(sessionStorage.getItem('estok.usuario')); } catch { /* Sessão antiga ou inválida. */ }
  const conectado = Boolean(sessionStorage.getItem('estok.accessToken'));
  const nome = conectado && usuario?.nome ? usuario.nome : 'Entre novamente';
  document.getElementById('sessao-nome').textContent = nome;
  document.getElementById('sessao-email').textContent = conectado ? usuario?.email || '' : '';
  document.getElementById('sessao-perfil').textContent = conectado
    ? (usuario?.perfil || sessionStorage.getItem('estok.perfil') || '') : 'Sessão não iniciada';
  document.getElementById('sessao-iniciais').textContent = conectado && usuario?.nome
    ? usuario.nome.trim().split(/\s+/).filter(Boolean).filter((_, i, partes) => i === 0 || i === partes.length - 1).map(p => p[0]).join('').toUpperCase() : '?';
}

document.getElementById('sair')?.addEventListener('click', async event => {
  event.currentTarget.disabled = true;
  try {
    const refresh = sessionStorage.getItem('estok.refreshToken');
    if (refresh) await cadastrar('/logout', { refresh_token: refresh });
  } catch { /* Encerra a sessão local mesmo quando a API está indisponível. */ }
  finally {
    for (const chave of ['estok.accessToken', 'estok.refreshToken', 'estok.perfil', 'estok.usuario']) sessionStorage.removeItem(chave);
    window.location.replace('/index.html');
  }
});

if (formForgotPassword) {
  const button = document.getElementById("btnForgotPassword");
  const emailInput = document.getElementById("emailForgotPassword");

  const camposNovaSenha = document.getElementById("camposNovaSenha");
  const inputSenha = document.getElementById("novaSenha");
  const inputConfirmar = document.getElementById("confirmarNovaSenha");
  const btnAlterar = document.getElementById("btnAlterarSenha");

  let usuarioEncontrado = null;

  let aviso = document.getElementById("login-feedback");

  if (!aviso) {
    aviso = document.createElement("p");
    aviso.id = "login-feedback";
    aviso.setAttribute("role", "alert");
    aviso.className = "text-sm text-red-300";
    formForgotPassword.append(aviso);
  }

  formForgotPassword.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = emailInput.value.trim();

    button.disabled = true;
    aviso.className = "text-sm text-red-300";
    aviso.textContent = "Verificando e-mail...";

    try {
      const response = await fetch(
        `${API_VM}/usuarios/buscarEmail/${encodeURIComponent(email)}`
      );

      if (!response.ok) {
        throw new Error("E-mail não encontrado.");
      }

      const data = await response.json();

      usuarioEncontrado = data;

      aviso.className = "text-sm text-green-400";
      aviso.textContent = "E-mail encontrado! Informe sua nova senha.";

      camposNovaSenha.classList.remove("hidden");
      camposNovaSenha.classList.add("flex");

      inputSenha.required = true;
      inputConfirmar.required = true;

      emailInput.disabled = true;
      button.disabled = true;

    } catch (error) {
      aviso.className = "text-sm text-red-300";
      aviso.textContent = error.message;

      button.disabled = false;
    }
  });

  btnAlterar.addEventListener("click", async () => {
    const senha = inputSenha.value;
    const confirmar = inputConfirmar.value;

    if (!senha || !confirmar) {
      aviso.textContent = "Preencha os dois campos.";
      aviso.className = "text-sm text-red-300";
      return;
    }

    if (senha !== confirmar) {
      aviso.textContent = "As senhas não coincidem.";
      aviso.className = "text-sm text-red-300";
      return;
    }

    btnAlterar.disabled = true;
    aviso.textContent = "Alterando senha...";

    try {
      const response = await fetch(
        `${API_VM}/usuarios/alterarSenha/${encodeURIComponent(usuarioEncontrado.email)}?nova_senha=${encodeURIComponent(senha)}`,
        {
          method: "PUT"
        }
      );

      const resultado = await response.json();

      if (!response.ok) {
        throw new Error(resultado.detail || "Erro ao alterar senha.");
      }

      aviso.className = "text-sm text-green-400";
      aviso.textContent = "Senha alterada com sucesso!";

    } catch (error) {
      aviso.className = "text-sm text-red-300";
      aviso.textContent = error.message;

    } finally {
      btnAlterar.disabled = false;
      window.location.replace("/");
    }
  });
}
