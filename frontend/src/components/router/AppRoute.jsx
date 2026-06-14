import { Navigate, useNavigate } from "react-router-dom";
import { canView, getPathByPageKey } from "../../navigation/catalog.jsx";

export default function AppRoute({ route, usuario }) {
  const navigate = useNavigate();
  const Component = route.component;

  function setActivePage(pageKey) {
    navigate(getPathByPageKey(pageKey));
  }

  if (!canView(route, usuario)) {
    return <Navigate to="/" replace />;
  }

  return <Component usuario={usuario} setActivePage={setActivePage} />;
}
