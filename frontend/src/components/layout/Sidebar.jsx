import { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ChevronDown, ChevronRight, Menu, X } from "lucide-react";
import { ROUTES, SIDEBAR_SECTIONS, canView } from "../../navigation/catalog.jsx";

function sectionHasActiveRoute(section, pathname) {
  return section.routes.some((route) => pathname === route.path || pathname.startsWith(`${route.path}/`));
}

function buildOpenSections(sections, pathname) {
  const initial = {};

  sections.forEach((section) => {
    initial[section.key] = section.key === "inicio" || sectionHasActiveRoute(section, pathname);
  });

  return initial;
}

export default function Sidebar({ usuario, open, setOpen }) {
  const location = useLocation();

  const visibleSections = useMemo(() => {
    return SIDEBAR_SECTIONS.map((section) => ({
      ...section,
      routes: ROUTES.filter((route) => section.items.includes(route.key) && canView(route, usuario)),
    })).filter((section) => section.routes.length > 0);
  }, [usuario]);

  const [openSections, setOpenSections] = useState(() => buildOpenSections(visibleSections, location.pathname));

  useEffect(() => {
    setOpenSections((current) => {
      const next = { ...current };
      visibleSections.forEach((section) => {
        if (sectionHasActiveRoute(section, location.pathname)) {
          next[section.key] = true;
        }
      });
      return next;
    });
  }, [location.pathname, visibleSections]);

  function toggleSection(sectionKey) {
    setOpenSections((current) => ({
      ...current,
      [sectionKey]: !current[sectionKey],
    }));
  }

  function closeMobileSidebar() {
    setOpen(false);
  }

  return (
    <>
      <button className="mobile-menu-button" onClick={() => setOpen(true)} aria-label="Abrir menu">
        <Menu size={22} />
      </button>

      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-header">
          <div>
            <h2>Farmácia Escola</h2>
            <span>Gestão do cuidado farmacêutico</span>
          </div>
          <button className="close-sidebar" onClick={() => setOpen(false)} aria-label="Fechar menu">
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav grouped" aria-label="Navegação principal">
          {visibleSections.map((section) => {
            const isSectionOpen = openSections[section.key] ?? false;
            const hasActiveChild = sectionHasActiveRoute(section, location.pathname);
            const panelId = `nav-section-${section.key}`;

            return (
              <div className="nav-section" key={section.key}>
                <button
                  type="button"
                  className={`nav-section-button ${hasActiveChild ? "active" : ""}`}
                  onClick={() => toggleSection(section.key)}
                  aria-expanded={isSectionOpen}
                  aria-controls={panelId}
                >
                  <span className="nav-section-title">{section.label}</span>
                  {isSectionOpen ? <ChevronDown size={17} /> : <ChevronRight size={17} />}
                </button>

                <div id={panelId} className="nav-section-items" hidden={!isSectionOpen}>
                  {section.routes.map((route) => {
                    const Icon = route.icon;
                    return (
                      <NavLink
                        key={route.key}
                        to={route.path}
                        end={route.path === "/"}
                        className={({ isActive }) => `nav-item nested ${isActive ? "active" : ""}`}
                        onClick={closeMobileSidebar}
                      >
                        <Icon size={18} />
                        <span>{route.label}</span>
                      </NavLink>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>
      </aside>

      {open && <div className="overlay" onClick={() => setOpen(false)} />}
    </>
  );
}
