import './style.css'

const form = document.getElementById("form");

form.addEventListener("submit", function (event) {
  event.preventDefault();

  const inputLogin = document.getElementById("email").value;
  const inputSenha = document.getElementById("password").value;
  if (inputLogin == "carlos@estok.com" && inputSenha == "senha") {
    alert("LOGOU")
    window.location.replace("http://localhost:5173/home.html");
  }
})
