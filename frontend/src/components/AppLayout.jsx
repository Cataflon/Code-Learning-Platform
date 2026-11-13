import { useCallback, useEffect, useLayoutEffect, useRef } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

import { homePathFor, useAuth } from "../auth/AuthContext.jsx";
import GlyphTideBackground from "./GlyphTideBackground.jsx";
import { Avatar, Logo } from "./ui.jsx";

// Square-cornered line icons, as in the prototype.
const ICONS = {
  dashboard: (
    <>
      <rect x="4" y="4" width="7" height="7" />
      <rect x="13" y="4" width="7" height="7" />
      <rect x="4" y="13" width="7" height="7" />
      <rect x="13" y="13" width="7" height="7" />
    </>
  ),
  courses: <path d="M5 5h14v12H9l-4 3z" />,
  learn: <path d="M12 6c-2-1.3-4.5-1.6-8-1.5v13c3.5-.1 6 .2 8 1.5 2-1.3 4.5-1.6 8-1.5v-13c-3.5-.1-6 .2-8 1.5zM12 6v13" />,
  report: <path d="M6 20v-6M12 20V5M18 20v-9" />,
  profile: <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21c1-4 4-6 8-6s7 2 8 6" />,
};

function NavIcon({ name }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" aria-hidden="true">
      {ICONS[name]}
    </svg>
  );
}

const STUDENT_NAV = [
  { to: "/dashboard", label: "Dashboard", short: "Dashboard", icon: "dashboard" },
  { to: "/courses", label: "Courses", short: "Courses", icon: "courses" },
  { to: "/learn", label: "Learn", short: "Learn", icon: "learn" },
  { to: "/report", label: "Concept report", short: "Report", icon: "report" },
];
const TEACHER_NAV = [
  { to: "/courses", label: "My courses", short: "Courses", icon: "courses" },
  { to: "/profile", label: "Profile", short: "Profile", icon: "profile" },
];

// The assignment page belongs to "Courses", the teacher's screens to "My courses".
function sectionOf(pathname) {
  if (pathname.startsWith("/assignments") || pathname.startsWith("/teacher")) return "/courses";
  return null;
}

function isCurrent(item, location) {
  const section = sectionOf(location.pathname);
  if (section) return item.to === section;
  return location.pathname === item.to || location.pathname.startsWith(`${item.to}/`);
}

/**
 * The underline under the active menu item. It slides to the item under the pointer and back
 * to the active one when the pointer leaves, like in the prototype.
 */
function useNavIndicator(location) {
  const navRef = useRef(null);
  const indRef = useRef(null);

  const moveTo = useCallback((link) => {
    const ind = indRef.current;
    if (!ind) return;
    if (!link) {
      ind.style.opacity = "0";
      return;
    }
    const pad = parseFloat(getComputedStyle(link).paddingLeft) || 0;
    ind.style.opacity = "1";
    ind.style.width = `${link.offsetWidth - pad * 2}px`;
    ind.style.transform = `translateX(${link.offsetLeft + pad}px)`;
  }, []);

  const reset = useCallback(
    () => moveTo(navRef.current?.querySelector('a[aria-current="page"]')),
    [moveTo],
  );

  useLayoutEffect(() => {
    reset();
  }, [location.pathname, reset]);

  useEffect(() => {
    window.addEventListener("resize", reset);
    document.fonts?.ready?.then(reset);
    return () => window.removeEventListener("resize", reset);
  }, [reset]);

  return { navRef, indRef, moveTo, reset };
}

/** Header, animated background, routed page and (on phones) the bottom navigation. */
export default function AppLayout() {
  const { user } = useAuth();
  const location = useLocation();
  const nav = user.role === "teacher" ? TEACHER_NAV : STUDENT_NAV;
  const { navRef, indRef, moveTo, reset } = useNavIndicator(location);

  return (
    <>
      <GlyphTideBackground />
      <div className="app">
        <header className="top">
          <div className="wrap">
            <Link to={homePathFor(user)} aria-label="Autograder home">
              <Logo />
            </Link>
            <nav className="nav" aria-label="Main" ref={navRef} onPointerLeave={reset} onBlur={reset}>
              <i className="nav-ind" aria-hidden="true" ref={indRef} />
              {nav.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  aria-current={isCurrent(item, location) ? "page" : undefined}
                  onPointerEnter={(event) => moveTo(event.currentTarget)}
                  onFocus={(event) => moveTo(event.currentTarget)}
                >
                  <NavIcon name={item.icon} />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </nav>
            <Link to="/profile" className="who" aria-label="Your profile">
              <span>
                <b>{user.full_name}</b>, {user.role}
              </span>
              <Avatar name={user.full_name} />
            </Link>
          </div>
        </header>
        <main className="page">
          <div className="wrap">
            {/* key: replays the short entry animation on every page change */}
            <div className="view" key={location.pathname}>
              <Outlet />
            </div>
          </div>
        </main>
        <nav className="tabbar" aria-label="Main" style={{ "--tabs": nav.length }}>
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              aria-current={isCurrent(item, location) ? "page" : undefined}
            >
              <NavIcon name={item.icon} />
              {item.short}
            </NavLink>
          ))}
        </nav>
      </div>
    </>
  );
}
