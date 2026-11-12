import { LogOut } from "lucide-react";

import { useAuth } from "../auth/AuthContext.jsx";
import { Button, Card, PageHeader } from "../components/ui.jsx";

const MENU = {
  student: ["See your assignments and deadlines", "Join a course with a code", "Submit code"],
  teacher: ["Create courses and assignments", "Add tests and concepts", "Follow submissions"],
};

/** Landing page after sign-in until the dashboards arrive in the next steps. */
export default function HomePage() {
  const { user, logout } = useAuth();
  const firstName = user.full_name.split(" ")[0];

  return (
    <>
      <PageHeader
        title={`Welcome back, ${firstName}!`}
        subtitle={`You are signed in as a ${user.role}.`}
        right={
          <Button variant="danger" onClick={logout}>
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Sign out
          </Button>
        }
      />
      <Card className="p-7">
        <h2 className="text-lg font-semibold">What you can do here</h2>
        <ul className="mt-4 list-inside list-disc space-y-2 text-muted">
          {MENU[user.role].map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Card>
    </>
  );
}
