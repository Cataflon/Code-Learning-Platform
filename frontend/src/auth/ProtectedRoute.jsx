import { Navigate, Outlet, useLocation } from "react-router-dom";

import { LoadingState } from "../components/states.jsx";
import { homePathFor, useAuth } from "./AuthContext.jsx";

/**
 * Guards the routes nested inside it.
 * No user -> /login. A user whose role is not in `roles` -> their own home page.
 */
export default function ProtectedRoute({ roles }) {
  const { user, status } = useAuth();
  const location = useLocation();

  if (status === "loading") return <LoadingState label="Signing you in…" />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (roles && !roles.includes(user.role)) return <Navigate to={homePathFor(user)} replace />;
  return <Outlet />;
}
