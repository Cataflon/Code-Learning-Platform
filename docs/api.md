# API

Generated from the OpenAPI schema by `python -m scripts.export_openapi`; do not edit by
hand. The interactive version is at `/docs` while the backend runs.

- Every route except `/health`, `/api/v1/config`, sign-in and registration needs
  `Authorization: Bearer <token>` (from `POST /api/v1/auth/login`).
- Errors have one shape: `{"detail": "...", "code": "..."}`. Invalid input answers
  422; another course's resources answer 404, a wrong role 403.
- Every answer carries `X-Request-ID`; a 429 also carries `Retry-After`.

## admin

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/admin/stats` | Get Stats | – | – | 200 `AdminStats` |
| `GET /api/v1/admin/users` | List Users | `q`, `role`, `active`, `limit`, `offset` | – | 200 `AdminUserPage` |
| `PATCH /api/v1/admin/users/{user_id}` | Update User | – | JSON `AdminUserUpdate` | 200 `AdminUserRead` |
| `POST /api/v1/admin/users/{user_id}/reset-password` | Reset Password | – | – | 200 `TemporaryPassword` |
| `GET /api/v1/admin/invite-codes` | List Invite Codes | – | – | 200 `list[InviteCodeRead]` |
| `POST /api/v1/admin/invite-codes` | Create Invite Code | – | JSON `InviteCodeCreate` | 201 `InviteCodeRead` |
| `POST /api/v1/admin/invite-codes/{invite_id}/revoke` | Revoke Invite Code | – | – | 200 `InviteCodeRead` |

## ai

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/config` | What the frontend needs to know about this server (whether to show the AI button). | – | – | 200 `ConfigRead` |
| `POST /api/v1/assignments/{assignment_id}/generate-tests` | Starts a job and answers 202 at once; poll GET /generation-jobs/{id} for progress. | – | JSON `GenerateTestsRequest` | 202 `JobCreated` |
| `GET /api/v1/generation-jobs/{job_id}` | Get Generation Job | – | – | 200 `GenerationJobRead` |
| `POST /api/v1/test-cases/{test_case_id}/approve` | Approve Test Case | – | – | 200 `TestCaseRead` |
| `POST /api/v1/assignments/{assignment_id}/tests/approve-all` | Approve All Tests | – | – | 200 `ApprovedCount` |

## assignments

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/courses/{course_id}/assignments` | List Assignments | `limit`, `offset` | – | 200 `list[AssignmentRead]` |
| `POST /api/v1/courses/{course_id}/assignments` | Create Assignment | – | JSON `AssignmentCreate` | 201 `AssignmentRead` |
| `GET /api/v1/assignments/{assignment_id}` | Get Assignment | – | – | 200 `AssignmentRead` |
| `PATCH /api/v1/assignments/{assignment_id}` | Update Assignment | – | JSON `AssignmentUpdate` | 200 `AssignmentRead` |
| `DELETE /api/v1/assignments/{assignment_id}` | Delete Assignment | – | – | 204 |
| `GET /api/v1/assignments/{assignment_id}/stats` | Pass rate per test and score distribution, from each student's best submission. | – | – | 200 `AssignmentStats` |

## auth

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `POST /api/v1/auth/register` | Register | – | JSON `RegisterRequest` | 201 `UserRead` |
| `POST /api/v1/auth/login` | Standard OAuth2 form: the ``username`` field carries the email. | – | form `Body_login_api_v1_auth_login_post` | 200 `TokenResponse` |

## concepts

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/courses/{course_id}/concepts` | List Concepts | – | – | 200 `list[ConceptRead]` |
| `POST /api/v1/courses/{course_id}/concepts` | Create Concept | – | JSON `ConceptCreate` | 201 `ConceptRead` |

## courses

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/courses` | List Courses | `limit`, `offset` | – | 200 `list[CourseRead]` |
| `POST /api/v1/courses` | Create Course | – | JSON `CourseCreate` | 201 `CourseRead` |
| `POST /api/v1/courses/join` | Join Course | – | JSON `JoinCourseRequest` | 200 `CourseRead` |
| `GET /api/v1/courses/{course_id}` | Get Course | – | – | 200 `CourseRead` |
| `PATCH /api/v1/courses/{course_id}` | Update Course | – | JSON `CourseUpdate` | 200 `CourseRead` |
| `DELETE /api/v1/courses/{course_id}` | Rows go by cascade; the material files are removed from disk after the commit. | – | – | 204 |
| `GET /api/v1/courses/{course_id}/students` | List Students | `limit`, `offset` | – | 200 `list[StudentRead]` |
| `DELETE /api/v1/courses/{course_id}/enrollment` | The student leaves the course; their submissions stay in the database. | – | – | 204 |
| `DELETE /api/v1/courses/{course_id}/students/{student_id}` | The teacher takes a student out of the course; their submissions stay. | – | – | 204 |
| `POST /api/v1/courses/{course_id}/join-code` | Generate another enrollment code; the old one stops working. | – | – | 200 `CourseRead` |
| `GET /api/v1/courses/{course_id}/stats` | Get Course Stats | – | – | 200 `CourseStats` |

## dashboard

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/me/dashboard` | Everything the student's start page shows, in one request. | – | – | 200 `StudentDashboard` |

## health

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /health` | Health | – | – | 200 `object` |

## materials

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/me/learn` | One card per enrolled course, with the number of materials and the latest upload. | – | – | 200 `list[LearnCourse]` |
| `GET /api/v1/courses/{course_id}/materials` | List Materials | – | – | 200 `list[MaterialRead]` |
| `POST /api/v1/courses/{course_id}/materials` | A PDF or a PPTX (multipart). A PPTX is converted to PDF before the answer, synchronously. | – | form `Body_upload_material_api_v1_courses__course_id__materials_post` | 201 `MaterialRead` |
| `GET /api/v1/materials/{material_id}` | Get Material | – | – | 200 `MaterialRead` |
| `PATCH /api/v1/materials/{material_id}` | Update Material | – | JSON `MaterialUpdate` | 200 `MaterialRead` |
| `DELETE /api/v1/materials/{material_id}` | Delete Material | – | – | 204 |
| `GET /api/v1/materials/{material_id}/file` | The original file, as an attachment, under its cleaned original name. | – | – | 200 |
| `GET /api/v1/materials/{material_id}/preview` | The PDF shown in the viewer (the original, or the PDF made from a PPTX), inline. | – | – | 200 |
| `GET /api/v1/assignments/{assignment_id}/materials` | Assignment Materials | – | – | 200 `list[MaterialLinkRead]` |
| `PUT /api/v1/assignments/{assignment_id}/materials` | Replace the whole list; materials from another course give 422. | – | JSON `list[MaterialLinkIn]` | 200 `list[MaterialLinkRead]` |
| `PUT /api/v1/test-cases/{test_case_id}/materials` | Set Test Case Materials | – | JSON `list[MaterialLinkIn]` | 200 `list[MaterialLinkRead]` |
| `GET /api/v1/submissions/{submission_id}/recommendations` | What to review for the failed tests of a submission; computed on demand. | – | – | 200 `RecommendationsRead` |
| `POST /api/v1/materials/{material_id}/reindex` | Extract the page text again (for materials uploaded before Step 9). | – | – | 200 `MaterialRead` |

## reports

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/courses/{course_id}/reports/concepts/me` | The student's own report: what they master and what they should review. | – | – | 200 `StudentConceptReport` |
| `GET /api/v1/courses/{course_id}/reports/concepts` | The whole class, per concept, for the course teacher. | – | – | 200 `ClassConceptReport` |

## submissions

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/assignments/{assignment_id}/submissions` | Student: their own attempts. Teacher: the class, filtered, searched and paginated. | `verdict`, `q`, `page`, `page_size` | – | 200 `SubmissionPage` |
| `POST /api/v1/assignments/{assignment_id}/submissions` | Answers 202 at once with status ``queued``; the tests run after the response is sent. | – | JSON `SubmissionCreate` | 202 `SubmissionRead` |
| `GET /api/v1/submissions/{submission_id}` | Get Submission | – | – | 200 `SubmissionRead` |

## test-cases

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/assignments/{assignment_id}/test-cases` | ``review=draft|approved`` filters the teacher's list; students only see approved tests. | `review` | – | 200 `list[TestCaseRead] | list[TestCasePublicRead]` |
| `POST /api/v1/assignments/{assignment_id}/test-cases` | Create Test Case | – | JSON `TestCaseCreate` | 201 `TestCaseRead` |
| `PATCH /api/v1/test-cases/{test_case_id}` | Update Test Case | – | JSON `TestCaseUpdate` | 200 `TestCaseRead` |
| `DELETE /api/v1/test-cases/{test_case_id}` | Delete Test Case | – | – | 204 |

## users

| Route | What it does | Query | Body | Answers |
| --- | --- | --- | --- | --- |
| `GET /api/v1/users/me` | Read Me | – | – | 200 `UserRead` |
| `PATCH /api/v1/users/me` | Update Me | – | JSON `UserUpdate` | 200 `UserRead` |
| `POST /api/v1/users/me/password` | Change My Password | – | JSON `PasswordChange` | 204 |
| `GET /api/v1/users/me/activity` | Submissions per day for the activity grid on the profile page, plus totals. | `weeks` | – | 200 `Activity` |

## Schemas

`Activity`, `ActivityDay`, `ActivityTotals`, `AdminStats`, `AdminUserPage`, `AdminUserRead`, `AdminUserUpdate`, `ApprovedCount`, `AssignmentCreate`, `AssignmentRead`, `AssignmentStats`, `AssignmentUpdate`, `Body_login_api_v1_auth_login_post`, `Body_upload_material_api_v1_courses__course_id__materials_post`, `ClassConceptReport`, `ClassConceptStat`, `ConceptCreate`, `ConceptRead`, `ConceptStat`, `ConceptTest`, `ConceptToReview`, `ConfigRead`, `CourseCreate`, `CourseRead`, `CourseStats`, `CourseUpdate`, `DashboardAssignment`, `DashboardCourse`, `DashboardStats`, `DashboardSubmission`, `FailedTest`, `FileType`, `GenerateTestsRequest`, `GenerationJobRead`, `HTTPValidationError`, `InviteCodeCreate`, `InviteCodeRead`, `JobCreated`, `JoinCourseRequest`, `LearnCourse`, `MaterialCategory`, `MaterialLinkIn`, `MaterialLinkRead`, `MaterialRead`, `MaterialUpdate`, `MaterialUsage`, `PasswordChange`, `Recommendation`, `RecommendationsRead`, `RegisterRequest`, `ResultBuckets`, `ReviewStatus`, `Role`, `ScoreBucket`, `StudentConceptReport`, `StudentDashboard`, `StudentRead`, `SubmissionCounts`, `SubmissionCreate`, `SubmissionPage`, `SubmissionRead`, `SubmissionStatus`, `SubmissionSummary`, `TemporaryPassword`, `TestCaseCreate`, `TestCasePublicRead`, `TestCaseRead`, `TestCaseUpdate`, `TestResultRead`, `TestStat`, `Thresholds`, `TokenResponse`, `UserRead`, `UserUpdate`, `ValidationError`, `Verdict`
