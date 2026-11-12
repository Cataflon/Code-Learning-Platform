import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { listAssignments } from "../api/assignments.js";
import * as coursesApi from "../api/courses.js";

export function useCourses() {
  return useQuery({ queryKey: ["courses"], queryFn: coursesApi.listCourses });
}

export function useCourse(courseId) {
  return useQuery({
    queryKey: ["course", courseId],
    queryFn: () => coursesApi.getCourse(courseId),
    enabled: courseId != null,
  });
}

export function useAssignments(courseId) {
  return useQuery({
    queryKey: ["assignments", courseId],
    queryFn: () => listAssignments(courseId),
    enabled: courseId != null,
  });
}

export function useJoinCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (joinCode) => coursesApi.joinCourse(joinCode),
    // Joining changes every per-course view: courses, dashboard, learn.
    onSuccess: () => queryClient.invalidateQueries(),
  });
}
