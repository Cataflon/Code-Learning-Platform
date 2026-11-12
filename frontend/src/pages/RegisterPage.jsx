import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import * as authApi from "../api/auth.js";
import { homePathFor, useAuth } from "../auth/AuthContext.jsx";
import AuthShell from "../components/AuthShell.jsx";
import { Button, FormError, TextField } from "../components/ui.jsx";

const ROLES = [
  { value: "student", label: "Student" },
  { value: "teacher", label: "Teacher" },
];

/** No mockup for this screen: same shell and components as Sign in. */
export default function RegisterPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    role: "student",
    invite_code: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={homePathFor(user)} replace />;

  const set = (field) => (event) => setForm((old) => ({ ...old, [field]: event.target.value }));
  const passwordTooShort = form.password.length > 0 && form.password.length < 8;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const payload = { ...form };
      if (payload.role !== "teacher") delete payload.invite_code;
      await authApi.register(payload);
      navigate("/login", { replace: true, state: { registered: true } });
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <AuthShell>
      <h2 className="text-4xl font-bold">Create account</h2>
      <p className="mt-3 text-muted">Join your courses and start submitting.</p>
      <form className="mt-8 space-y-5" onSubmit={handleSubmit} noValidate>
        <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Account type">
          {ROLES.map((role) => (
            <button
              key={role.value}
              type="button"
              role="radio"
              aria-checked={form.role === role.value}
              onClick={() => setForm((old) => ({ ...old, role: role.value }))}
              className={
                "rounded-lg border px-4 py-2.5 text-sm font-semibold " +
                (form.role === role.value
                  ? "border-accent-soft bg-accent-tint text-accent-soft"
                  : "border-line text-muted hover:text-ink")
              }
            >
              {role.label}
            </button>
          ))}
        </div>
        <TextField
          label="Full name"
          autoComplete="name"
          value={form.full_name}
          onChange={set("full_name")}
          required
        />
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="name@student.utcluj.ro"
          value={form.email}
          onChange={set("email")}
          required
        />
        <TextField
          label="Password"
          type="password"
          autoComplete="new-password"
          placeholder="At least 8 characters"
          value={form.password}
          onChange={set("password")}
          error={passwordTooShort ? "Use at least 8 characters." : ""}
          required
        />
        {form.role === "teacher" && (
          <TextField
            label="Invite code"
            value={form.invite_code}
            onChange={set("invite_code")}
            hint="Teacher accounts need the code from the platform administrator."
            required
          />
        )}
        <FormError>{error}</FormError>
        <Button
          type="submit"
          size="lg"
          className="w-full"
          disabled={busy || !form.full_name || !form.email || form.password.length < 8}
        >
          {busy ? "Creating…" : "Create account"}
        </Button>
      </form>
      <p className="mt-8 text-center text-muted">
        Already have an account?{" "}
        <Link to="/login" className="font-semibold text-accent-soft hover:text-white">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
