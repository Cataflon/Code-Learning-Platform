import { useQuery } from "@tanstack/react-query";

import * as materialsApi from "../api/materials.js";

export function useLearn() {
  return useQuery({ queryKey: ["learn"], queryFn: materialsApi.getLearn });
}

export function useCourseMaterials(courseId) {
  return useQuery({
    queryKey: ["materials", courseId],
    queryFn: () => materialsApi.listMaterials(courseId),
    enabled: courseId != null,
  });
}

export function useMaterial(materialId) {
  return useQuery({
    queryKey: ["material", materialId],
    queryFn: () => materialsApi.getMaterial(materialId),
  });
}

export function useAssignmentMaterials(assignmentId) {
  return useQuery({
    queryKey: ["assignment-materials", assignmentId],
    queryFn: () => materialsApi.getAssignmentMaterials(assignmentId),
  });
}
