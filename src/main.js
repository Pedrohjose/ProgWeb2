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
      const response = await fetch(`http://40.127.11.169:8000/buscar-id/${encodeURIComponent(email)}`, {
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

const formForgotPassword = document.getElementById("formForgotPassword");

if (formForgotPassword) {
  formForgotPassword.addEventListener("submit", async (event) => {
    event.preventDefault();

    const button = document.getElementById("btnForgotPassword");
    const email = document.getElementById("emailForgotPassword").value;

    let aviso = document.getElementById("login-feedback");

    if (!aviso) {
      aviso = document.createElement("p");
      aviso.id = "login-feedback";
      aviso.setAttribute("role", "alert");
      aviso.className = "text-sm text-red-300";
      formForgotPassword.append(aviso);
    }

    button.disabled = true;
    aviso.textContent = "Verificando e-mail...";

    try {
      const response = await fetch(
        `http://40.127.11.169:8000/usuarios/buscarEmail/${encodeURIComponent(email)}`
      );

      if (!response.ok) {
        throw new Error("E-mail não encontrado.");
      }

      const data = await response.json();

      aviso.className = "text-sm text-green-400";
      aviso.textContent = "E-mail encontrado! Informe sua nova senha.";

      if (document.getElementById("camposNovaSenha")) {
        return;
      }

      const container = document.createElement("div");
      container.id = "camposNovaSenha";
      container.className = "flex flex-col gap-3";

      const labelSenha = document.createElement("label");
      labelSenha.textContent = "Nova senha";
      labelSenha.className = "text-sm";

      const inputSenha = document.createElement("input");
      inputSenha.type = "password";
      inputSenha.id = "novaSenha";
      inputSenha.placeholder = "Digite sua nova senha";
      inputSenha.required = true;
      inputSenha.className = "w-full rounded-md p-2 text-black";

      const labelConfirmar = document.createElement("label");
      labelConfirmar.textContent = "Confirmar nova senha";
      labelConfirmar.className = "text-sm";

      const inputConfirmar = document.createElement("input");
      inputConfirmar.type = "password";
      inputConfirmar.id = "confirmarSenha";
      inputConfirmar.placeholder = "Confirme sua nova senha";
      inputConfirmar.required = true;
      inputConfirmar.className = "w-full rounded-md p-2 text-black";

      const btnAlterar = document.createElement("button");
      btnAlterar.type = "button";
      btnAlterar.id = "btnAlterarSenha";
      btnAlterar.textContent = "Alterar senha";
      btnAlterar.className = "w-full rounded-md p-2";

      container.append(
        labelSenha,
        inputSenha,
        labelConfirmar,
        inputConfirmar,
        btnAlterar
      );

      formForgotPassword.append(container);

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

        btnAlterar.addEventListener("click", async () => {
          const senha = inputSenha.value;
          const confirmar = inputConfirmar.value;

          if (!senha || !confirmar) {
            aviso.textContent = "Preencha os dois campos.";
            return;
          }

          if (senha !== confirmar) {
            aviso.textContent = "As senhas não coincidem.";
            return;
          }

          btnAlterar.disabled = true;
          aviso.textContent = "Alterando senha...";

          try {
            const response = await fetch(
              `http://40.127.11.169:8000/usuarios/${data.id}`,
              {
                method: "PUT",
                headers: {
                  "Content-Type": "application/json",
                  "Authorization": `Bearer ${seuToken}`
                },
                body: JSON.stringify({
                  nome: data.nome,
                  email: data.email,
                  senha: senha,
                  perfil: data.perfil
                })
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
          }
        });

        console.log("ID do usuário:", data.id);
        console.log("Nova senha:", senha);
      });

    } catch (error) {
      aviso.className = "text-sm text-red-300";
      aviso.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}
