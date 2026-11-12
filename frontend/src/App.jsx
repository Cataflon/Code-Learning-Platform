import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, homePathFor, useAuth } from "./auth/AuthContext.jsx";
import ProtectedRoute from "./auth/ProtectedRoute.jsx";
import AppLayout from "./components/AppLayout.jsx";
import AssignmentPage from "./pages/AssignmentPage.jsx";
import CoursesPage from "./pages/CoursesPage.jsx";
import CoursePage from "./pages/CoursePage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import StatusPage from "./pages/StatusPage.jsx";
import StudentDashboard from "./pages/StudentDashboard.jsx";
import AssignmentEditor from "./pages/teacher/AssignmentEditor.jsx";
import SubmissionsPage from "./pages/teacher/SubmissionsPage.jsx";
import TeacherCoursesPage from "./pages/teacher/TeacherCoursesPage.jsx";

/** Same path, different page per role. */
function ByRole({ student, teacher }) {
  const { user } = useAuth();
  return user.role === "teacher" ? teacher : student;
}

function RootRedirect() {
  const { user } = useAuth();
  return <Navigate to={user ? homePathFor(user) : "/login"} replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/status" element={<StatusPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<RootRedirect />} />
          <Route
            path="/courses"
            element={<ByRole student={<CoursesPage />} teacher={<TeacherCoursesPage />} />}
          />
          <Route path="/profile" element={<ProfilePage />} />
          <Route element={<ProtectedRoute roles={["student"]} />}>
            <Route path="/dashboard" element={<StudentDashboard />} />
            <Route path="/assignments/:assignmentId" element={<AssignmentPage />} />
          </Route>
          <Route element={<ProtectedRoute roles={["teacher"]} />}>
            <Route path="/courses/:courseId" element={<CoursePage />} />
            <Route path="/teacher/assignments/:assignmentId/edit" element={<AssignmentEditor />} />
            <Route
              path="/teacher/assignments/:assignmentId/submissions"
              element={<SubmissionsPage />}
            />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
}

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Do not hammer the server on errors the user caused (403, 404, 422).
        retry: (failureCount, error) => !(error?.status >= 400 && error?.status < 500) && failureCount < 2,
        staleTime: 10_000,
        refetchOnWindowFocus: false,
      },
    },
  });
}

export default function App() {
  const [queryClient] = useState(createQueryClient);
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
