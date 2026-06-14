import Login from "../../pages/login.jsx";

export default function RequireAuth({ usuario, setUsuario, children }) {
  if (!usuario) {
    return <Login onLogin={setUsuario} />;
  }

  return children;
}
