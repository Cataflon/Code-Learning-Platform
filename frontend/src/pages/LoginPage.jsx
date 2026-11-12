import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { homePathFor, useAuth } from "../auth/AuthContext.jsx";
import AuthShell from "../components/AuthShell.jsx";
import { Button, FormError, TextField } from "../components/ui.jsx";

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={homePathFor(user)} replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const me = await login(email, password);
      navigate(location.state?.from ?? homePathFor(me), { replace: true });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <AuthShell>
      <h2 className="text-4xl font-bold">Welcome back</h2>
      <p className="mt-3 text-muted">Sign in to continue your assignments.</p>
      {location.state?.registered && (
        <p className="mt-4 rounded-lg border border-pass-line bg-pass-tint px-4 py-3 text-sm text-pass">
          Account created. You can sign in now.
        </p>
      )}
      <form className="mt-8 space-y-6" onSubmit={handleSubmit} noValidate>
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="name@student.utcluj.ro"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <div className="relative">
          <TextField
            label="Password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            placeholder="At least 8 characters"
            inputClassName="pr-12"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
          <button
            type="button"
            className="absolute right-3 top-[42px] p-1 text-muted hover:text-ink"
            onClick={() => setShowPassword((shown) => !shown)}
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
          </button>
        </div>
        <FormError>{error}</FormError>
        <Button type="submit" size="lg" className="w-full" disabled={busy || !email || !password}>
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </form>
      <p className="mt-8 text-center text-muted">
        No account?{" "}
        <Link to="/register" className="font-semibold text-accent-soft hover:text-white">
          Create one
        </Link>
      </p>
    </AuthShell>
  );
}
