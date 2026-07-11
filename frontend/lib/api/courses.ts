import { apiRequest } from "./client";

export function listCourses() {
  return apiRequest<{ courses: Array<Record<string, unknown>> }>("/courses");
}

export function getCourse(courseSlug: string) {
  return apiRequest<Record<string, unknown>>(`/courses/${courseSlug}`);
}

export function getCourseSections(courseId: number) {
  return apiRequest<{ sections: Array<Record<string, unknown>> }>(`/courses/${courseId}/sections`);
}

export function getSectionUnits(sectionId: number) {
  return apiRequest<{ units: Array<Record<string, unknown>> }>(`/sections/${sectionId}/units`);
}

export function getUnit(unitId: number) {
  return apiRequest<Record<string, unknown>>(`/units/${unitId}`);
}

export function getUnitGuidebook(unitId: number) {
  return apiRequest<Record<string, unknown>>(`/units/${unitId}/guidebook`);
}
