import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, homePathFor, useAuth } from "./auth/AuthContext.jsx";
import ProtectedRoute from "./auth/ProtectedRoute.jsx";
import AppLayout from "./components/AppLayout.jsx";
import { LoadingState } from "./components/states.jsx";
import AssignmentPage from "./pages/AssignmentPage.jsx";
import CoursesPage from "./pages/CoursesPage.jsx";
import CoursePage from "./pages/CoursePage.jsx";
import Learn from "./pages/Learn.jsx";
import LandingPage from "./pages/LandingPage.jsx";
import LearnCourse from "./pages/LearnCourse.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import MaterialViewer from "./pages/MaterialViewer.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import ConceptReport from "./pages/ConceptReport.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import StatusPage from "./pages/StatusPage.jsx";
import StudentDashboard from "./pages/StudentDashboard.jsx";
import AssignmentEditor from "./pages/teacher/AssignmentEditor.jsx";
import ClassConceptReport from "./pages/teacher/ClassConceptReport.jsx";
import MaterialsPage from "./pages/teacher/MaterialsPage.jsx";
import StudyMaterialsEditor from "./pages/teacher/StudyMaterialsEditor.jsx";
import SubmissionsPage from "./pages/teacher/SubmissionsPage.jsx";
import TeacherCoursesPage from "./pages/teacher/TeacherCoursesPage.jsx";
import AdminInvitesPage from "./pages/admin/AdminInvitesPage.jsx";
import AdminUsersPage from "./pages/admin/AdminUsersPage.jsx";

/** Same path, different page per role. */
function ByRole({ student, teacher }) {
  const { user } = useAuth();
  if (user.role === "admin") return <Navigate to={homePathFor(user)} replace />;
  return user.role === "teacher" ? teacher : student;
}

/** "/": the landing page for visitors, the home page of their role for signed-in users. */
function Home() {
  const { user, status } = useAuth();
  if (status === "loading") return <LoadingState label="Signing you in…" />;
  return user ? <Navigate to={homePathFor(user)} replace /> : <LandingPage />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/status" element={<StatusPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route
            path="/courses"
            element={<ByRole student={<CoursesPage />} teacher={<TeacherCoursesPage />} />}
          />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/learn/materials/:materialId" element={<MaterialViewer />} />
          <Route element={<ProtectedRoute roles={["student"]} />}>
            <Route path="/dashboard" element={<StudentDashboard />} />
            <Route path="/assignments/:assignmentId" element={<AssignmentPage />} />
            <Route path="/report" element={<ConceptReport />} />
            <Route path="/learn" element={<Learn />} />
            <Route path="/learn/courses/:courseId" element={<LearnCourse />} />
          </Route>
          <Route element={<ProtectedRoute roles={["admin"]} />}>
            <Route path="/admin/users" element={<AdminUsersPage />} />
            <Route path="/admin/invites" element={<AdminInvitesPage />} />
          </Route>
          <Route element={<ProtectedRoute roles={["teacher"]} />}>
            <Route path="/courses/:courseId" element={<CoursePage />} />
            <Route path="/courses/:courseId/report" element={<ClassConceptReport />} />
            <Route path="/courses/:courseId/materials" element={<MaterialsPage />} />
            <Route path="/teacher/assignments/:assignmentId/materials" element={<StudyMaterialsEditor />} />
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
