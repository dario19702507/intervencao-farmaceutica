import { useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { findRouteByPath } from "../../navigation/catalog.jsx";

export default function RouteTelemetry({ usuario }) {
  const location = useLocation();
  const enteredAt = useRef(Date.now());
  const previous = useRef(null);

  useEffect(() => {
    const route = findRouteByPath(location.pathname);
    const now = Date.now();

    if (previous.current) {
      window.dispatchEvent(
        new CustomEvent("frontend_route_leave", {
          detail: {
            routeKey: previous.current.routeKey,
            path: previous.current.path,
            durationMs: now - enteredAt.current,
          },
        })
      );
    }

    enteredAt.current = now;
    previous.current = { routeKey: route.key, path: location.pathname };

    window.dispatchEvent(
      new CustomEvent("frontend_page_view", {
        detail: {
          routeKey: route.key,
          telemetryKey: route.telemetryKey,
          path: location.pathname,
          perfil: usuario?.perfil || null,
          timestamp: new Date().toISOString(),
        },
      })
    );
  }, [location.pathname, usuario?.perfil]);

  return null;
}
