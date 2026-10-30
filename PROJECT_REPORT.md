# HackEval AI
## Extended Academic Project Report

**50-page submission edition**  
**Formatting note:** This edition is structured for approximately 50 pages when
placed in a college report template using 12-point text, 1.5 line spacing,
normal margins, diagrams, screenshots, tables, and the appendices supplied
below. Page breaks may be inserted at each major chapter heading.

**Project type:** College major project / software engineering MVP  
**Report date:** 20 October 2026  
**System name:** HackEval AI  
**Repository:** Automated-Evaluation-Engine

---

## 1. Executive Summary

HackEval AI is a role-aware hackathon management and intelligent project-evaluation
platform. It brings event organizers, participants, judges, and administrators
into one workspace for creating hackathons, forming teams, submitting projects,
reviewing repositories, evaluating submissions, and publishing leaderboard data.

The system combines conventional workflow automation with explainable evaluation
signals. Repository health, static analysis, text analysis, fraud-risk indicators,
and rubric-based scoring are presented as decision-support evidence rather than
as an automatic replacement for human judges. The platform also provides a
separate sandbox runner for controlled execution of submitted programs.

The project is implemented as a full-stack application with a React and
TypeScript frontend, a FastAPI backend, optional PostgreSQL and Redis services,
and a separately containerized execution runner. It can run locally through
Docker Compose and has Terraform configuration for a Google Cloud deployment.

## 2. Problem Statement

Hackathons often manage registration, teams, submissions, judging, and results
through disconnected tools. This creates several problems:

- organizers have limited visibility into event progress;
- participants lack a consistent submission workflow;
- judges must manually inspect repositories and project evidence;
- evaluation criteria can be applied inconsistently;
- suspicious submission patterns are difficult to identify;
- running untrusted code directly on an application server introduces security
  and operational risk.

HackEval AI addresses these problems through a single workflow-oriented platform
with role-based access, structured data, explainable scoring, audit-oriented
updates, and an isolated execution boundary.

## 3. Objectives

The project objectives are:

1. Provide a responsive dashboard for the main hackathon roles.
2. Support hackathon, team, submission, upload, and judging workflows.
3. Enforce authentication and role-based authorization.
4. Analyze GitHub repository metadata and code/project evidence.
5. Produce bounded, rubric-based, explainable evaluation results.
6. Surface fraud and plagiarism-related signals for human review.
7. Prevent participant code from running inside the API process.
8. Support both local development and production-oriented cloud deployment.
9. Preserve a transparent fallback when an external AI provider is unavailable
   or returns invalid data.

## 4. Scope

### Included

- User registration and JWT login.
- Participant, organizer, judge, and admin roles.
- Hackathon creation and listing.
- Team creation, membership, and invite-code joining.
- Project submission and artifact upload.
- GitHub repository analysis.
- Static code and text artifact analysis.
- AI-assisted evaluation through a validated provider adapter.
- Deterministic demo evaluation fallback.
- Fraud-risk reporting and review flags.
- Judge scoring and leaderboard/export views.
- Isolated Python, JavaScript, Java, and C++ test execution.
- PostgreSQL schema migration and JSON fallback storage.
- Redis-ready rate limiting.
- Docker Compose and Google Cloud Terraform deployment foundation.

### Not included as a production guarantee

- Automatic acceptance or rejection of submissions solely by the platform.
- Guaranteed plagiarism detection. Current fraud output is a review signal.
- Full multi-instance coordination when the in-process rate limiter is used.
- Asynchronous media processing and enterprise-scale object-storage workflows.
- A production-ready AI provider; provider integration is configurable.

## 5. System Architecture

```text
                    +----------------------+
                    | React + TypeScript   |
                    | Vite dashboard       |
                    +----------+-----------+
                               |
                               | REST / JSON
                               v
                    +----------------------+
                    | FastAPI application  |
                    | JWT + role checks    |
                    +--+-------+-------+---+
                       |       |       |
             +---------+       |       +----------------+
             |                 |                        |
             v                 v                        v
       PostgreSQL/       Evaluation and           Isolated runner
       JSON storage      analysis services       Python/Node/Java/C++
             |
             +-------------------+
             | Redis (optional)  |
             | shared rate limit |
             +-------------------+

       Optional external integrations:
       GitHub API, AI provider, Google Cloud Storage, Google Cloud services
```

### Major components

| Component | Responsibility |
| --- | --- |
| `frontend/` | React dashboard, authentication screen, role-aware views, forms, analytics, leaderboard, and settings |
| `backend/app/` | FastAPI application, API routers, schemas, authentication, storage, database access, and services |
| `backend/app/services/repository.py` | GitHub repository metadata and documentation analysis |
| `backend/app/services/analysis.py` | Static code and text artifact analysis |
| `backend/app/services/evaluation.py` | Rubric scoring, provider validation, and demo fallback |
| `backend/app/services/fraud.py` | Explainable risk signals and review recommendations |
| `backend/app/services/sandbox.py` | Safe API adapter to the external runner |
| `runner/` | Restricted execution service using fixed language toolchains |
| `infra/gcp/` | Terraform foundation for Cloud Run, Cloud SQL, Redis, storage, networking, and secrets |

## 6. Functional Design

### 6.1 Authentication and authorization

The backend uses bcrypt password hashing and JWT access tokens. Every protected
route can require one or more roles. The supported roles are:

- **Participant:** create teams, join teams, upload artifacts, and submit projects.
- **Organizer:** create and manage hackathons, review event activity, and export results.
- **Judge:** review submissions, run evaluations, and record manual scores.
- **Admin:** access platform-level dashboards and administrative operations.

Request bodies use Pydantic validation for fields such as email, password,
URLs, score ranges, rubric weights, list sizes, and text lengths.

### 6.2 Hackathon and team management

Organizers can define event metadata, dates, registration limits, team-size
limits, rules, and a scoring rubric. Participants can create teams, add members,
and join using an invite code. Dashboard routes expose organizer, judge, and
admin views, while leaderboard and CSV export routes support result reporting.

### 6.3 Submission workflow

A submission contains project identity and narrative information, technologies,
GitHub and optional live-demo links, and uploaded artifact identifiers. The
submission workflow is designed to preserve evidence that can be reviewed by
judges and used by analysis services.

### 6.4 Explainable evaluation

The default rubric includes Innovation, Technical Complexity, Functionality,
Impact, UI/UX & Design, and Presentation. Each criterion has a weight and a
bounded score. Evaluation output includes:

- overall score;
- criterion-level scores and reasons;
- strengths and weaknesses;
- recommendation;
- explanatory text;
- model mode (`configured_provider` or `demo_fallback`).

When an AI provider is configured, its response is validated for required fields,
rubric alignment, score bounds, and text types. Invalid or incomplete provider
responses are not treated as trusted evaluations; the system explicitly returns
the deterministic demo fallback instead.

### 6.5 Repository, code, and artifact analysis

The repository service reads GitHub metadata such as languages, repository tree
size, commit activity, contributors, README quality, archived state, issues,
and recent activity. These signals are converted into a bounded repository
health score and explanatory notes. Additional services analyze source structure
and text artifacts such as pitches and demos.

### 6.6 Fraud-risk review

The fraud service calculates bounded signals for similarity risk, commit
anomalies, repository age, and submission consistency. The result includes
reasons and a `human_review_required` flag. These values are deliberately
described as review indicators rather than definitive plagiarism findings.

### 6.7 Isolated code execution

The API does not execute participant code. It sends an artifact identifier and
structured tests to the separate runner service. The runner:

- accepts only a fixed set of languages;
- rejects caller-provided shell commands;
- reads source artifacts from a controlled input volume or object storage;
- applies source and test-input size limits;
- uses a temporary working directory;
- enforces a short execution timeout;
- returns per-test output, exit code, and pass/fail status.

Docker Compose further isolates the runner with a read-only container, dropped
capabilities, no-new-privileges, memory and CPU limits, a process limit, and an
internal network.

## 7. Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, TypeScript, Vite |
| Backend | Python 3.11+, FastAPI, Pydantic |
| Authentication | JWT, PyJWT, bcrypt/passlib |
| Persistence | SQLAlchemy, PostgreSQL, Alembic; JSON fallback for local development |
| Rate limiting | In-process fixed-window limiter; Redis implementation for shared deployments |
| HTTP integrations | HTTPX, GitHub API, configurable AI provider |
| Execution | Separate FastAPI runner with Python, Node.js, Java, and C++ toolchains |
| Local orchestration | Docker Compose |
| Cloud foundation | Google Cloud Run, Cloud SQL, Memorystore Redis, Cloud Storage, Secret Manager, Terraform |
| Testing | Pytest, opt-in deployed-service integration checks |

## 8. Security and Reliability Considerations

The implementation includes several security-focused controls:

- role checks on protected API routes;
- password hashing rather than plaintext password storage;
- configurable JWT secret and production validation against default secrets;
- request validation and bounded inputs;
- authentication rate limiting;
- explicit refusal to run untrusted code in the API process;
- runner token authentication;
- fixed execution toolchains and timeouts;
- container resource and privilege restrictions;
- documented secret handling for cloud deployment.

The system also favors explicit failure behavior. For example, an unavailable
sandbox raises a clear configuration error, and an invalid AI provider response
is marked as a fallback rather than silently persisted as a trusted result.

## 9. Testing and Verification

The backend test suite covers:

- repository report generation and explainability;
- bounded evaluation and fraud-risk scores;
- valid configured AI-provider responses;
- invalid-provider fallback behavior;
- authentication rate limits;
- production JWT-secret validation;
- Redis atomic-counter behavior.

The cloud integration tests are intentionally opt-in. When enabled, they check
that the deployed API health endpoint and deployed frontend are reachable.

Recommended verification commands:

```powershell
cd backend
pytest -q tests/test_services.py tests/test_security.py

cd ..\frontend
npm run build
```

For a deployed environment, configure `RUN_CLOUD_INTEGRATION_TESTS`,
`CLOUD_API_URL`, and `CLOUD_FRONTEND_URL`, then run:

```powershell
cd backend
pytest -q tests/test_cloud_integration.py
```

## 10. Expected Outcomes

The completed MVP provides:

1. A unified hackathon operating workspace.
2. Consistent role-specific workflows.
3. Reproducible rubric-based scoring.
4. Explainable evidence for judges and organizers.
5. A safer boundary for evaluating submitted programs.
6. A path from local development to cloud deployment.

The most important design outcome is transparency: automated scores and risk
signals support human decisions and expose their reasoning instead of presenting
opaque or irreversible decisions.

## 11. Limitations

The current implementation remains an MVP. Key limitations include:

- local JSON storage remains available for development and is not a substitute
  for a managed production data strategy;
- the in-process limiter does not coordinate across API replicas;
- repository analysis depends on GitHub availability, permissions, and API limits;
- the demo evaluator is deterministic and should not be represented as a
  production machine-learning model;
- fraud signals are heuristic and require human review;
- uploaded pitch and video processing is not yet asynchronous;
- full production observability, alerting, backup verification, and secret
  rotation still require operational configuration;
- the runner is a controlled foundation and should be deployed with hardened
  container and network policies.

## 12. Future Enhancements

Recommended next steps are:

1. Add asynchronous workers for repository, media, and evaluation jobs.
2. Move all production uploads to versioned object storage.
3. Add persistent evaluation and fraud-report history with richer audit trails.
4. Introduce a managed queue and shared Redis rate limiting for multi-instance deployments.
5. Add configurable organization-level rubrics and judging calibration.
6. Improve repository comparison with approved reference sets and explainable
   similarity evidence.
7. Add automated frontend and API contract tests.
8. Add structured logs, metrics, tracing, alerting, and backup-restore drills.
9. Harden the runner with rootless execution, stronger network isolation, and
   per-language resource policies.
10. Add participant notifications, feedback workflows, and accessibility testing.

## 13. Conclusion

HackEval AI demonstrates a practical full-stack approach to hackathon
operations and intelligent project evaluation. Its strongest contribution is
the combination of workflow management, explainable automated evidence, and a
separate execution service that keeps untrusted code away from the main API
process. The modular service boundaries and cloud deployment foundation make it
appropriate as a college major-project MVP and provide a clear path toward a
more scalable production platform.

---

# Extended Academic Chapters

## 14. Certificate

This is to certify that the project report entitled **“HackEval AI: An
Explainable Hackathon Management and Intelligent Project-Evaluation
Platform”** is a bonafide record of the project work carried out as part of
the academic requirements for the award of the relevant undergraduate degree.
The work presented in this report was developed using React, TypeScript,
FastAPI, Python, SQLAlchemy, PostgreSQL-compatible relational design, Docker,
and Terraform.

The project demonstrates the application of software engineering principles to
a realistic event-management problem. It includes requirements analysis,
database design, REST API development, user-interface development, validation,
testing, security controls, and deployment planning. The system is presented
as an academic MVP and not as an unconditional production certification
service. Automated scores and risk indicators remain subject to human review.

**Project guide:** ____________________  
**Student name:** ____________________  
**Roll number:** ____________________  
**Department:** ____________________  
**Institution:** ____________________  
**Academic year:** 2026–2027  
**Date:** ____________________

## 15. Declaration

I declare that this project report is an original presentation of the design
and implementation work completed for HackEval AI. The report describes the
software that exists in the project repository, identifies the components that
are MVP adapters, and records the limitations that must be addressed before a
public production deployment.

The project does not claim that an algorithm can determine plagiarism,
quality, or winner selection without human judgment. Where external services
such as GitHub or a configurable AI provider are used, their responses are
validated and their availability is treated as an operational dependency. The
deterministic evaluator is labelled as a demo fallback rather than being
represented as a trained machine-learning model.

## 16. Acknowledgement

The completion of this project required the combined application of web
development, backend engineering, database design, software security, testing,
and cloud deployment concepts. The project team acknowledges the guidance of
the project supervisor and the academic department for providing the
opportunity to work on a practical software system.

We also acknowledge the maintainers of the open-source technologies used in the
implementation, including React, TypeScript, Vite, FastAPI, Pydantic, HTTPX,
SQLAlchemy, Alembic, PostgreSQL, Redis, Docker, and Terraform. These tools
provided reusable foundations while the project focused on domain workflows,
validation, explainability, and safe execution boundaries.

## 17. Abstract

Hackathons are collaborative events in which participants propose, build, and
demonstrate software within a limited period. A typical event requires
registration management, team formation, submission collection, repository
inspection, judging, fraud review, and result publication. When these
activities are performed using disconnected forms, spreadsheets, chat
messages, and manual scripts, organizers lose visibility and judges receive
inconsistent evidence.

HackEval AI addresses this operational gap through a role-aware platform. It
provides separate workflows for participants, organizers, judges, and
administrators. The platform stores hackathons, teams, submissions, uploads,
and audit records. It analyzes public GitHub repository metadata, produces
bounded rubric-based scores, reports explainable fraud-risk indicators, and
provides a separate runner interface for controlled code execution.

The architecture separates the API process from untrusted program execution.
The API only sends structured requests to an externally configured runner. The
runner accepts a fixed language allow-list and structured tests, while the
deployment configuration applies resource and privilege restrictions. This
separation reduces the blast radius of submitted code.

The result is an extensible MVP rather than a replacement for human judges.
Its key contribution is transparent decision support: every automated output
has a mode, a reason, a bounded score, and a stated limitation.

**Keywords:** hackathon management, explainable evaluation, FastAPI, React,
role-based access control, repository analysis, sandbox execution, fraud-risk
signals, Docker, cloud deployment.

## 18. Table of Contents

1. Executive Summary  
2. Problem Statement  
3. Objectives  
4. Scope  
5. System Architecture  
6. Functional Design  
7. Technology Stack  
8. Security and Reliability  
9. Testing and Verification  
10. Expected Outcomes  
11. Limitations  
12. Future Enhancements  
13. Conclusion  
14. Certificate  
15. Declaration  
16. Acknowledgement  
17. Abstract  
18. Table of Contents  
19. List of Figures and Tables  
20. Introduction  
21. Background and Motivation  
22. Existing-System Study  
23. Proposed-System Study  
24. Feasibility Analysis  
25. Requirements Engineering  
26. User Roles and Use Cases  
27. Detailed Workflow Design  
28. Architecture and Module Design  
29. Frontend Design  
30. Backend and API Design  
31. Database Design  
32. Evaluation Methodology  
33. Repository and Text Analysis  
34. Fraud-Risk Methodology  
35. Secure Sandbox Design  
36. Security Threat Model  
37. Deployment and DevOps  
38. Test Plan and Results  
39. Performance and Reliability  
40. User Experience and Accessibility  
41. Ethical and Responsible-AI Considerations  
42. Project Management  
43. Cost and Resource Analysis  
44. Results and Discussion  
45. Limitations and Risk Register  
46. Future Development Roadmap  
47. Conclusion and Learning Outcomes  
48. References  
49. Appendix A: API Catalogue  
50. Appendix B: Test Cases and Presentation Checklist

## 19. List of Figures and Tables

### Figures

1. High-level system architecture  
2. Role-to-workflow relationship  
3. Submission lifecycle  
4. Evaluation-service interaction  
5. Isolated runner boundary  
6. Deployment topology  
7. Entity relationship overview  
8. Authentication sequence  
9. Evaluation fallback sequence  
10. Suggested dashboard screenshot layout

### Tables

1. Technology stack  
2. Stakeholder requirements  
3. Functional requirements  
4. Non-functional requirements  
5. Role permissions  
6. Core entities  
7. Evaluation rubric  
8. Threat and mitigation register  
9. Test case matrix  
10. Risk register

## 20. Introduction

Software projects used in educational and innovation events are judged under
time pressure. The judging process must balance creativity, technical
implementation, user value, presentation quality, and evidence from the
repository. A platform that only collects a final form cannot provide this
context. Conversely, an automated platform that produces one opaque number can
create a false impression of objectivity.

HackEval AI is designed around the middle path. It automates repetitive
workflow operations and organizes evidence, while keeping judges responsible
for the final decision. A participant can create or join a team, describe a
project, connect a GitHub repository, and upload supporting artifacts. An
organizer can create a hackathon with dates, team limits, rules, and a rubric.
A judge can inspect submissions, review repository signals, see automated
explanations, and record a manual evaluation.

The platform is intentionally modular. Authentication, storage, analysis,
evaluation, fraud reporting, and sandbox integration are represented as
separate services or boundaries. This makes it possible to replace local JSON
storage with PostgreSQL, replace the demo evaluator with a validated provider,
or deploy the runner as a hardened service without rewriting the user-facing
workflow.

## 21. Background and Motivation

The growth of student and developer hackathons has increased the number of
projects that must be reviewed in a short period. Manual processes have four
recurring weaknesses:

1. **Fragmented evidence:** repository links, slides, demos, and judge notes
   are stored in different places.
2. **Inconsistent criteria:** judges interpret the same rubric differently
   when criteria are not represented in the software.
3. **Limited auditability:** organizers cannot easily determine who changed a
   score or when a submission moved to a new state.
4. **Unsafe execution:** running submitted code inside the main web server can
   expose credentials, files, or network access.

The motivation for HackEval AI is therefore not “replace the judge.” It is to
give every judge the same structured evidence and to make the system's
automated behaviour inspectable. The project treats explainability and safety
as first-class requirements, not as documentation added after implementation.

## 22. Existing-System Study

The existing process for a small event commonly uses an online form for
registration, a spreadsheet for teams, a drive folder for presentations, and
chat messages for coordination. Repository review is performed manually, and
final scores are often entered into another spreadsheet. This approach is easy
to start but becomes difficult to operate when the number of teams grows.

Commercial event platforms provide some of these capabilities, but they may be
costly, difficult to customize for academic rubrics, or unsuitable for
experiments with evaluation services. A custom MVP provides control over data
models, validation, deployment, and the boundary between automation and
human review.

The project does not attempt to reproduce every enterprise event feature. It
selects a practical subset: identity, roles, event configuration, team
membership, submissions, artifact references, repository analysis, evaluation,
fraud review, leaderboard support, and controlled runner integration.

## 23. Proposed-System Study

The proposed system uses one authenticated REST API as the coordination point
for the web client and independent services. The frontend is responsible for
displaying role-specific views and collecting validated input. The backend
enforces authorization and validation rather than trusting the client.

The proposed flow is:

1. A user registers or signs in.
2. The API issues a time-limited JWT containing identity and role claims.
3. An organizer creates a hackathon and defines its rubric.
4. Participants create or join a team.
5. A team creates a submission and attaches evidence.
6. A judge requests repository, text, or evaluation analysis.
7. The system returns bounded, explainable outputs.
8. The judge records a manual evaluation and the organizer publishes results.

External dependencies are isolated behind adapters. GitHub analysis is
performed through a repository service, AI evaluation is optional, and code
execution is delegated to the runner. If the AI provider is unavailable or
returns invalid data, a deterministic fallback is returned with an explicit
`demo_fallback` mode.

## 24. Feasibility Analysis

### 24.1 Technical feasibility

The project is technically feasible because it uses widely supported
technologies and well-defined HTTP boundaries. React and Vite provide a fast
frontend development cycle. FastAPI and Pydantic provide typed request
validation and OpenAPI documentation. SQLAlchemy and Alembic allow the
relational schema to evolve. Docker Compose makes the local stack reproducible,
while Terraform captures a production-oriented Google Cloud foundation.

### 24.2 Operational feasibility

The interface maps to familiar event roles and uses standard flows. An
organizer does not need to understand the internals of the evaluator to create
a rubric. A judge sees criterion-level reasons rather than an unexplained
score. Administrators receive platform-level access without giving every user
the same privileges.

### 24.3 Economic feasibility

The MVP can run locally using open-source software. A small deployment can use
managed database, object storage, and container services, but costs will vary
with usage. Optional AI calls and repository API usage are the principal
variable costs. A deterministic fallback allows demonstrations and development
without a paid model provider.

### 24.4 Schedule feasibility

The work can be divided into discovery, design, backend, frontend, security,
testing, and deployment phases. The module boundaries reduce the risk that a
change to one integration blocks the complete demonstration.

## 25. Requirements Engineering

### 25.1 Stakeholder requirements

| Stakeholder | Need | System response |
| --- | --- | --- |
| Participant | Register and submit a project | Authenticated participant workflow |
| Team | Collaborate under one submission | Team membership and invite code |
| Organizer | Configure and operate an event | Hackathon, rubric, dashboard, export |
| Judge | Review consistent evidence | Evaluation, repository report, manual score |
| Administrator | Operate the platform | Admin role and platform views |
| Institution | Demonstrate engineering quality | Tests, documentation, deployment plan |

### 25.2 Functional requirements

FR-01: The system shall register users with validated names, emails, passwords,
and roles.  
FR-02: The system shall authenticate users and issue bearer tokens.  
FR-03: The system shall restrict protected routes by role.  
FR-04: Organizers shall create hackathons with dates, rules, team limits, and
rubrics.  
FR-05: Participants shall create and join teams.  
FR-06: Teams shall create submissions with project narrative and repository
links.  
FR-07: The system shall retain artifact identifiers and audit events.  
FR-08: The system shall analyze supported public GitHub repositories.  
FR-09: The system shall return criterion-level evaluation explanations.  
FR-10: The system shall mark invalid provider output as a fallback.  
FR-11: Judges shall record manual scores and comments.  
FR-12: The system shall return fraud-risk signals with a human-review flag.  
FR-13: The API shall refuse local execution of untrusted code.  
FR-14: The system shall support leaderboard and export-oriented views.

### 25.3 Non-functional requirements

| Category | Requirement |
| --- | --- |
| Security | Hash passwords, validate input, enforce roles, isolate execution |
| Reliability | Explicit errors and deterministic fallback behaviour |
| Maintainability | Separate routers, schemas, stores, and services |
| Performance | Short HTTP timeouts and bounded input sizes |
| Portability | Local Docker Compose and cloud-oriented Terraform |
| Usability | Role-aware dashboard with understandable labels |
| Auditability | Manual judge updates produce audit records |
| Scalability | PostgreSQL and Redis-ready deployment design |

## 26. User Roles and Use Cases

### 26.1 Participant use cases

Participants register, log in, view available hackathons, create a team, join
with an invite code, prepare a submission, attach artifacts, and submit the
project. Validation prevents incomplete narratives, invalid URLs, excessive
technology lists, and oversized text fields.

### 26.2 Organizer use cases

Organizers create events, define registration and submission windows, set
maximum participants and team size, publish rules, define rubric weights, view
event activity, inspect flagged submissions, and export results. The organizer
is responsible for the event configuration; the evaluator does not invent
criteria outside the configured rubric.

### 26.3 Judge use cases

Judges review the submission narrative, inspect repository health, read
criterion-level automated reasons, review fraud signals, run allowed tests
through the isolated runner, and record a final manual score. The interface
should show the difference between automated recommendation and judge decision.

### 26.4 Administrator use cases

Administrators manage platform-level access, inspect operational health, and
support deployment or moderation workflows. The administrator role is not
automatically treated as a judge or organizer role; permissions should remain
explicit.

## 27. Detailed Workflow Design

### 27.1 Authentication workflow

The client sends validated registration or login data to the authentication
router. The backend hashes a password using bcrypt, stores only the hash, and
returns a JWT after successful verification. The token includes a subject, role,
and expiry. Protected dependencies decode the token and apply role checks.
Authentication endpoints are rate limited to reduce repeated credential
attempts.

### 27.2 Submission lifecycle

The intended lifecycle is:

`DRAFT -> SUBMITTED -> UNDER_REVIEW -> EVALUATED -> ACCEPTED/REJECTED`

`FLAGGED` is an additional review state when fraud indicators or moderation
checks require attention. A draft may be edited; a submitted item should be
treated as evidence with a clear timestamp. A judge may evaluate only after
the required submission data is available.

### 27.3 Evidence workflow

Evidence consists of project text, technologies, a GitHub URL, an optional live
demo URL, and artifact identifiers. Artifact content is deliberately separated
from the submission record so that object storage can be introduced later.
Analysis services receive controlled data and return reports without changing
the source evidence.

## 28. Architecture and Module Design

The backend follows a layered organization:

* **Routers** expose HTTP endpoints and convert validated requests into service
  calls.
* **Schemas** define input and output contracts.
* **Core modules** contain configuration, security, and rate limiting.
* **Store and database modules** manage persistence choices.
* **Services** contain repository, evaluation, fraud, analysis, storage, and
  sandbox logic.

This structure prevents the frontend from depending on database details and
prevents provider-specific code from being spread across route handlers. It
also allows unit tests to target evaluation and analysis functions without
starting the complete web application.

The frontend is a Vite application with React components and TypeScript data
models. The dashboard groups overview, hackathons, submissions, leaderboard,
analytics, and settings rather than presenting every API operation as a
separate technical screen.

## 29. Frontend Design

The frontend is designed around information hierarchy. The overview screen
should answer: how many hackathons are active, how many submissions need
attention, and what is the current judging status? The submissions screen
should make status and evidence visible before opening detail. The leaderboard
should distinguish published results from provisional automated scores.

TypeScript is used to make API response assumptions visible during development.
Reusable cards, tables, forms, navigation, and status badges reduce visual
inconsistency. Responsive CSS allows the dashboard to remain usable on laptop
and smaller screens. The interface should avoid presenting the model score as
an unquestionable verdict; labels such as “recommendation,” “risk signal,” and
“human review required” are part of the UX.

Suggested screenshots for the final printed report are:

1. Login and role selection screen.
2. Organizer overview dashboard.
3. Hackathon creation form.
4. Submission detail and evidence panel.
5. Evaluation criteria and explanation panel.
6. Leaderboard and analytics screen.

## 30. Backend and API Design

FastAPI provides route declaration, dependency injection, request parsing, and
OpenAPI documentation. Pydantic constraints are used at the boundary:
passwords have bounded lengths, project fields have minimum content, URLs are
parsed as HTTP URLs, scores remain between zero and one hundred, and lists have
maximum sizes.

Representative endpoint groups are:

| Group | Purpose |
| --- | --- |
| `/api/auth` | Registration, login, current-user identity |
| `/api/hackathons` | Event creation, listing, configuration |
| `/api/teams` | Team creation, joining, membership |
| `/api/submissions` | Submission creation, updates, review |
| `/api/dashboard` | Role-specific aggregate views |
| `/api/evaluation` | Automated and manual evaluation |
| `/api/sandbox` | Structured request to the external runner |
| `/api/uploads` | Upload metadata and artifact references |

The API must not trust role values sent by the browser. Roles are read from
the authenticated token and checked by backend dependencies. Errors are
returned explicitly so that a client can distinguish invalid input,
unauthorized access, unavailable external services, and internal failures.

## 31. Database Design

The relational design creates tables through the Alembic migration using the
application metadata. The principal entities are users, hackathons, teams,
team members, submissions, uploads, and audit logs. Foreign-key relationships
preserve ownership and event membership.

| Entity | Important attributes | Relationship |
| --- | --- | --- |
| User | id, name, email, password hash, role | owns or joins teams |
| Hackathon | id, name, dates, rules, rubric, status | contains teams/submissions |
| Team | id, name, invite code, hackathon id | has members and submissions |
| Submission | project text, URLs, status, team id | reviewed by judges |
| Upload | id, storage key, type, size | referenced by submission |
| Audit event | actor, action, target, timestamp | records important updates |

For local development, the JSON store keeps the demonstration easy to run.
For deployment, `DATABASE_URL` selects the relational database and Alembic
applies the schema. The report treats the fallback as a development convenience,
not as a substitute for transactional production persistence.

## 32. Evaluation Methodology

The default rubric contains six criteria:

| Criterion | Weight |
| --- | ---: |
| Innovation | 20 |
| Technical Complexity | 25 |
| Functionality | 20 |
| Impact | 15 |
| UI/UX & Design | 10 |
| Presentation | 10 |

Weights sum to 100. Each criterion receives a bounded score from zero to one
hundred. The weighted overall score is calculated as:

`overall = sum(criterion_score × criterion_weight / 100)`

The deterministic demo evaluator uses project-description length and bounded
repository-health signals to create reproducible criteria. It then produces
strengths, weaknesses, recommendation, explanation, and `model_mode`. This is
useful for local demonstrations because it does not require network access or a
paid model.

When an AI provider is configured, the response must contain all required
fields, match the rubric criteria in order, provide valid score ranges, and
use non-empty explanatory text. A malformed response is rejected and the
fallback is returned. This behaviour is safer than persisting an incomplete
provider response.

## 33. Repository and Text Analysis

The repository service accepts only GitHub URLs with an owner and repository
path. It retrieves repository metadata, language statistics, a recursive tree,
commit count, contributor count, and README content. It calculates a bounded
health score using activity, contributors, README quality, archived status,
and open issues.

The service intentionally reports that lines of code are unavailable when the
GitHub API does not expose a repository-wide metric. This is an important
example of honest reporting: the system does not fabricate a LOC value simply
because a report field is convenient.

The static analysis adapter reports maintainability, security, complexity,
documentation, and architecture metrics derived from available repository
signals. Its mode is explicitly `mvp_adapter`. Production work should connect
language-specific linters, dependency scanners, test coverage, and secret
detection tools, while retaining provenance for every finding.

Text analysis measures content completeness and extracts expected sections such
as Problem, Solution, Features, Technology, and Impact. It does not claim to
understand video or visual slide quality; those are future service boundaries.

## 34. Fraud-Risk Methodology

Fraud reporting is deliberately a risk model rather than a verdict. The
current report includes similarity risk, commit anomaly, repository age signal,
and submission consistency. These values are bounded and combined into an
overall risk score. A medium or high signal sets `human_review_required`.

The service gives judges actionable reasons, such as reviewing token or
structure similarity against approved reference repositories. It also
communicates that commit activity and repository structure are only evidence.
A new repository is not proof of misconduct, and a high commit count is not
proof of originality.

An improved production model should use approved reference sets, transparent
similarity evidence, temporal analysis, author identity checks, and an appeal
workflow. Any such system must be evaluated for false positives and must
avoid penalizing legitimate use of frameworks, tutorials, or team templates.

## 35. Secure Sandbox Design

The API never invokes a shell, Docker daemon, or participant program. It sends
language, source archive identifier, and structured tests to a separate runner.
The runner accepts Python, JavaScript, Java, and C++ only. It does not accept a
caller-provided shell command.

The deployment design uses a read-only source volume, temporary working
directories, short timeouts, CPU and memory limits, a process limit, dropped
Linux capabilities, no-new-privileges, and network restrictions. In production,
the runner should execute rootlessly and should not have access to the host
Docker socket.

The security boundary is both technical and organizational. The API reports a
clear `SandboxUnavailable` error when the runner is not configured instead of
silently running the code locally. This prevents a development convenience
from becoming a production vulnerability.

## 36. Security Threat Model

The main assets are user credentials, submission evidence, private operational
data, judge scores, runner infrastructure, and the integrity of leaderboard
results. Key threats include credential stuffing, token theft, unauthorized
role escalation, malicious uploads, unsafe code execution, provider response
tampering, and abuse of external API quotas.

Mitigations include bcrypt password hashing, JWT expiry, role checks, bounded
Pydantic input, rate limiting, separate runner authentication, resource
quotas, explicit provider validation, and secret configuration through the
environment or a secret manager.

The model should be reviewed before public deployment. HTTPS termination,
secure cookies if browser sessions are introduced, CSRF considerations,
database least privilege, upload content scanning, structured audit logs,
dependency updates, and security monitoring require operational ownership.

## 37. Deployment and DevOps

Docker Compose supports local PostgreSQL, Redis, API, runner, and frontend
services. The frontend can be built by Vite and served through the configured
web server. The API container runs migrations as part of the documented local
startup path.

The Google Cloud Terraform foundation describes Cloud Run services, Cloud SQL,
Memorystore Redis, Cloud Storage, VPC access, and Secret Manager bindings.
This separation allows stateless API replicas while persistent services hold
data and shared rate-limit state.

A deployment pipeline should include:

1. dependency installation and lockfile verification;
2. backend unit tests;
3. frontend type-check/build;
4. container image build;
5. migration validation;
6. deployment to a non-production environment;
7. smoke tests for health, authentication, and critical routes;
8. approval before production promotion.

## 38. Test Plan and Results

Testing focuses on boundaries where incorrect behaviour would damage trust:
score limits, provider validation, fallback selection, password and token
security, repository input validation, fraud report bounds, and runner refusal.

The backend test suite includes service and security tests. Cloud tests are
opt-in so that ordinary local test runs do not require deployed URLs. Frontend
build verification confirms that TypeScript and Vite can produce a distributable
application.

The recommended local verification is:

```powershell
cd backend
pytest -q tests/test_services.py tests/test_security.py
cd ..\frontend
npm run build
```

Test results should be copied into the final college submission with the date,
Python version, Node version, operating system, and command used. A screenshot
of the passing test summary may be included as evidence, but the command and
raw result remain more reproducible than a screenshot alone.

## 39. Performance and Reliability

External calls use timeouts: repository metadata requests use bounded HTTP
windows, provider evaluation has a short timeout, and runner requests have a
maximum duration. This prevents an unavailable dependency from holding a web
request indefinitely.

Performance work for a larger event should move repository analysis,
large-file processing, video extraction, and evaluation into asynchronous jobs.
The API should return a job identifier and expose status rather than keeping a
browser request open. Caching repository reports for a short period can reduce
GitHub API use, while invalidation is needed when a submission changes.

Reliability also depends on clear failure semantics. An unavailable GitHub
service is not an empty repository. An unavailable runner is not a passing
test. An invalid AI response is not a trusted score. The implementation
preserves these distinctions through explicit errors and mode fields.

## 40. User Experience and Accessibility

The user interface should use readable contrast, visible focus states,
keyboard-accessible controls, descriptive form errors, and status labels that
do not rely only on colour. Long project descriptions and evaluation reasons
should remain readable through appropriate spacing and line length.

Accessibility is especially important for judging workflows. A judge may need
to compare several submissions quickly, so criterion labels, weights, scores,
and explanations should be consistently positioned. Risk signals should be
presented with explanatory text and not as alarming colour-only indicators.

The final project demonstration should include a keyboard navigation check, a
small viewport check, and validation of empty, invalid, and over-limit form
states. These checks are inexpensive and improve confidence in the interface.

## 41. Ethical and Responsible-AI Considerations

Automated evaluation can reproduce bias from its inputs or provider. A
repository with fewer commits may be a legitimate sprint project; a polished
README may not prove technical quality. Therefore, the system does not
automatically accept or reject a team. Judges must be able to inspect evidence,
override a recommendation, and record reasons.

The system should disclose when a score comes from `configured_provider` and
when it comes from `demo_fallback`. Provider prompts and responses should be
stored only when permitted by the event's privacy policy. Personal data should
be minimized, access should be logged, and participants should know what
repository and submission information is analyzed.

Fairness evaluation should include different project sizes, languages, team
structures, repository histories, and writing styles. Any new similarity
detector must provide an appeal path and must not label a participant as a
plagiarist from a heuristic score alone.

## 42. Project Management

The project can be managed through incremental milestones:

| Phase | Main deliverable |
| --- | --- |
| Discovery | Problem definition, users, scope, constraints |
| Design | Architecture, database, workflows, API contracts |
| Backend | Auth, roles, CRUD flows, service adapters |
| Frontend | Dashboard, forms, role-aware navigation |
| Safety | Validation, rate limiting, runner boundary |
| Verification | Unit tests, build checks, integration smoke tests |
| Deployment | Docker Compose and cloud infrastructure documentation |
| Reporting | Screenshots, results, limitations, future roadmap |

Each phase should produce a reviewable artifact. This keeps the report aligned
with implementation and reduces the risk of writing claims that cannot be
demonstrated.

## 43. Cost and Resource Analysis

Local development requires a modern browser, Node.js, Python, and optionally
Docker Desktop. A small cloud deployment requires a container runtime,
relational database, object storage, and optionally Redis. Costs depend on
instance size, storage, outbound traffic, repository usage, and AI-provider
calls.

The MVP reduces cost in three ways: it supports local JSON development, it
uses a deterministic evaluation fallback, and it delegates expensive
operations to optional services. Production operators should set budgets,
quotas, log retention, and provider limits before enabling public access.

Human resources include a full-stack developer, a reviewer familiar with
security, and an event administrator. The last role is important because
rubrics, moderation rules, and participant support cannot be fully automated.

## 44. Results and Discussion

The implemented MVP meets the core objective of bringing event operations and
evaluation evidence into one platform. The frontend provides the expected
dashboard areas, while the backend exposes role-aware workflows and validated
service boundaries. Repository and text adapters produce explainable reports,
and the evaluation service supports both a configured provider and a
deterministic fallback.

The most significant result is architectural rather than numerical. Untrusted
code is not executed by the API, invalid model output is not trusted, and
fraud signals are not described as proof. These choices improve the integrity
of a judging platform even before advanced analytics are introduced.

The result should be interpreted as an MVP demonstration. It is not evidence
that the heuristic scores correlate with expert judge scores at scale.
Validation with real, consented event data would be required before using
automated scores for high-impact decisions.

## 45. Limitations and Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| GitHub API limit | Repository analysis delayed | Configure token, cache, retry policy |
| AI provider outage | Automated evaluation unavailable | Explicit deterministic fallback |
| JSON storage misuse | Data loss or concurrency issues | Use PostgreSQL in production |
| Runner misconfiguration | Tests unavailable or unsafe | Fail closed; separate service |
| False fraud signal | Participant unfairly flagged | Human review and appeal |
| In-process rate limit | Uneven multi-instance protection | Move counters to Redis |
| Large uploads | Slow requests and disk pressure | Object storage and async jobs |
| Weak deployment secrets | Account compromise | Secret Manager and rotation |

The largest conceptual limitation is measurement. A bounded score is not the
same as a validated quality metric. The system therefore exposes evidence and
reasoning so that future experiments can compare outputs against calibrated
human judgments.

## 46. Future Development Roadmap

### Short term

Add API contract tests, improve frontend loading and error states, persist
evaluation history, add structured logs, and document database backup and
restore procedures.

### Medium term

Introduce a queue for repository and artifact analysis, use object storage for
uploads, move all rate limiting to Redis, add configurable organization
rubrics, and provide participant feedback after judging.

### Long term

Add calibrated judge assistance, approved reference repositories, language-
specific static analysis, rootless runner pools, observability dashboards,
multi-tenant organization boundaries, accessibility certification, and formal
fairness evaluation of automated signals.

Each roadmap item should preserve the project's central principles: bounded
inputs, explicit failure modes, provenance, human review, and safe isolation.

## 47. Conclusion and Learning Outcomes

HackEval AI is a practical demonstration of how a complex event workflow can
be decomposed into understandable software components. The project combines a
React dashboard, a validated FastAPI API, role-aware authorization, relational
schema planning, explainable analysis services, and a separate runner boundary.

The major learning outcomes are:

1. translating stakeholder needs into functional and non-functional
   requirements;
2. designing a REST API with typed contracts and role checks;
3. separating domain services from transport and storage;
4. handling unreliable external providers explicitly;
5. treating untrusted code execution as a separate security problem;
6. writing tests for score bounds, authentication, and fallback behaviour;
7. documenting local and cloud deployment paths;
8. communicating limitations instead of overstating automation.

The project is ready for academic demonstration and further engineering. Its
production path depends on asynchronous processing, hardened operations,
persistent audit history, privacy controls, and validation against real human
judging outcomes.

## 48. References

1. FastAPI documentation, API framework and dependency injection concepts.
2. Pydantic documentation, typed validation and constrained request models.
3. React documentation, component-based user interface development.
4. TypeScript documentation, static typing for frontend application code.
5. Vite documentation, frontend build and development tooling.
6. SQLAlchemy documentation, Python database mapping and persistence.
7. Alembic documentation, relational schema migration management.
8. PostgreSQL documentation, relational database concepts and transactions.
9. Docker documentation, container images, isolation, and resource controls.
10. Terraform documentation, declarative cloud infrastructure management.
11. GitHub REST API documentation, repository metadata and tree endpoints.
12. OWASP Application Security Verification Standard, web security controls.
13. OWASP Top 10, common web application risks.
14. Python documentation, language and standard-library references.

The final submitted report should add the institution's required citation
style, access dates, project repository URL, and any papers consulted during
implementation.

## 49. Appendix A: API Catalogue

The following catalogue is a presentation aid. The authoritative interface is
the generated FastAPI OpenAPI document.

| Method | Resource | Access | Purpose |
| --- | --- | --- | --- |
| POST | `/api/auth/register` | Public | Create a validated account |
| POST | `/api/auth/login` | Public | Verify credentials and issue JWT |
| GET | `/api/auth/me` | Authenticated | Return current identity |
| GET | `/api/hackathons` | Authenticated | List available events |
| POST | `/api/hackathons` | Organizer | Create an event |
| POST | `/api/teams` | Participant | Create a team |
| POST | `/api/teams/join` | Participant | Join with invite code |
| POST | `/api/submissions` | Participant | Create project submission |
| GET | `/api/submissions` | Judge/Organizer | Review submissions |
| POST | `/api/evaluation` | Judge | Request evaluation |
| POST | `/api/evaluation/manual` | Judge | Record manual score |
| POST | `/api/sandbox/run` | Judge | Request isolated tests |
| POST | `/api/analysis/repository` | Judge/Organizer | Analyze GitHub evidence |
| POST | `/api/analysis/text` | Judge/Organizer | Analyze text evidence |
| GET | `/api/dashboard` | Role-specific | Return dashboard aggregates |

Every endpoint should document authentication, expected request shape, success
response, validation errors, authorization errors, and external-service
failures. The report demonstration should show the interactive `/docs` page
for the running API.

## 50. Appendix B: Test Cases and Presentation Checklist

### B.1 Test case matrix

| ID | Scenario | Expected result |
| --- | --- | --- |
| TC-01 | Register with short password | Validation error |
| TC-02 | Login with correct credentials | Bearer token returned |
| TC-03 | Login repeatedly beyond limit | Rate-limit response |
| TC-04 | Participant opens organizer route | Authorization failure |
| TC-05 | Invalid GitHub host | Repository validation error |
| TC-06 | Provider returns missing fields | Demo fallback |
| TC-07 | Provider returns score above 100 | Demo fallback |
| TC-08 | Fraud report with normal input | Bounded report and reasons |
| TC-09 | Sandbox URL is absent | Explicit unavailable error |
| TC-10 | Unsupported language requested | Request validation error |
| TC-11 | Valid submission evaluation | Criteria and overall score |
| TC-12 | Frontend production build | Build completes successfully |

### B.2 Demonstration sequence

1. Start the services using Docker Compose or the documented local commands.
2. Open the frontend and demonstrate the login screen.
3. Sign in using a demo role and show the dashboard.
4. Create or open a hackathon and explain its rubric.
5. Show a team and submission record.
6. Open repository analysis and explain health-score fields.
7. Run evaluation and point out criterion reasons and model mode.
8. Show a fraud report and explain why it requires human review.
9. Attempt sandbox execution without a runner and show the fail-closed error.
10. Show the API documentation and test summary.

### B.3 Report formatting checklist

* Add institution logo and title page.
* Replace blank certificate fields with approved names.
* Add screenshots captured from the running application.
* Render the architecture and entity diagrams as figures.
* Insert page breaks at major chapters.
* Apply the institution's font, margin, header, footer, and citation rules.
* Add signed declaration and supervisor approval if required.
* Include the final test output and deployment screenshots.

This appendix makes the report reproducible: a reviewer can follow the same
sequence, inspect the same evidence, and distinguish implemented behaviour from
future work.

### B.4 Viva questions and answers

**Q1. Why is the evaluator not fully automatic?**  
Automated analysis can organize evidence and provide consistent suggestions,
but it cannot reliably understand every project context or make a fair final
decision. The platform therefore gives judges criterion-level explanations and
keeps the final decision with a human reviewer.

**Q2. What happens when the AI provider is unavailable?**  
The service returns a deterministic, bounded demo evaluation and marks its
`model_mode` as `demo_fallback`. It does not pretend that a provider was used.

**Q3. Why is code execution a separate service?**  
Submitted programs are untrusted. Running them inside the API process could
expose application files, credentials, or network access. A separately
containerized runner allows resource limits, a fixed language allow-list, and
an independent security policy.

**Q4. Why is PostgreSQL preferred over the JSON fallback?**  
PostgreSQL provides transactions, concurrent access, indexes, constraints, and
backup options. JSON storage is useful for local demonstrations but is not
appropriate as the authoritative store for a multi-instance production event.

**Q5. How does the system prevent a participant from becoming an organizer?**  
The browser does not control authorization. The API reads the role from the
authenticated token and applies backend dependencies to protected routes.
Client-side navigation improves usability, but it is not a security boundary.

**Q6. Does a high fraud score prove plagiarism?**  
No. The report is intentionally a review signal. A judge must examine the
repository, team history, project evidence, and any approved comparison
material before reaching a conclusion.

## Appendix C: Implementation Notes

### C.1 Validation boundaries

Validation is applied at multiple boundaries because different failures have
different meanings. Pydantic validates the shape and size of incoming JSON.
Authentication dependencies validate the token and identity. Service functions
validate external assumptions such as GitHub URL shape and provider response
fields. Storage code is responsible for persistence errors. This layered
approach avoids placing all trust in one layer.

Examples of deliberate limits include a password maximum of 128 characters,
project descriptions capped at 4,000 characters, a maximum of 15 technologies,
and a maximum of 50 structured sandbox tests. These limits reduce accidental
resource exhaustion and make error behaviour predictable.

### C.2 External provider validation

An external provider may return valid JSON with the wrong semantic structure.
For example, it may omit a criterion, use a score of 150, or return a string
where a list is expected. The evaluation adapter checks:

1. the response is an object;
2. an OpenAI-compatible response contains a usable first choice;
3. required top-level fields are present;
4. the number and order of criteria match the rubric;
5. every score is numeric and bounded;
6. strengths and weaknesses are lists of strings;
7. recommendation and explanation are non-empty strings.

Only after all checks pass is the provider mode returned. Otherwise the
provider failure is included in the fallback explanation. This design creates
a useful audit trail without exposing provider credentials in the response.

### C.3 Storage evolution

The application supports a staged storage strategy. During early development,
the JSON fallback reduces setup time and allows a student to demonstrate the
workflow on a laptop. The relational migration creates the durable schema
needed for shared environments. The production transition should include a
data migration script, a backup, a rollback plan, and a verification query for
users, submissions, and audit events.

Uploads require a similar transition. Local file paths are acceptable for a
development demonstration, but production files should be stored in private
object storage with generated keys, content-type checks, size quotas, malware
scanning, and signed download URLs. A database row should record metadata and
not expose an untrusted local path to the browser.

### C.4 Auditability

An audit event should answer five questions: who acted, what action occurred,
which object was affected, when it happened, and what relevant change was
made. Manual judge updates are particularly important because leaderboard
integrity depends on the ability to reconstruct score changes. In a mature
deployment, audit records should be append-only for ordinary application
users, retained according to the event policy, and visible to authorized
organizers or administrators.

## Appendix D: Deployment Runbook

### D.1 Local preparation

1. Install Python 3.11 or a compatible tested version, Node.js 20+, and
   Docker Desktop if the complete stack is required.
2. Clone the repository and inspect the environment example files.
3. Create the Python virtual environment and install backend requirements.
4. Install frontend packages and run the frontend build.
5. Configure a development JWT secret and local service URLs.
6. Start PostgreSQL and Redis if relational or shared-rate-limit behaviour is
   being tested.
7. Apply the Alembic migration before using the relational backend.

### D.2 Smoke checks

The first smoke check is the health endpoint. The second is account creation
and login. The third is an authenticated dashboard request. The fourth is
creation of a hackathon and submission. The fifth is an analysis request using
a controlled public repository or a mocked service response. The sixth is a
deliberate sandbox request without a configured runner, which must fail closed.

Smoke checks should be run after every deployment because a service can be
“running” while a required dependency, migration, or environment variable is
missing. The result should record timestamp, environment, build identifier,
and outcome.

### D.3 Production checklist

* Replace all development secrets with Secret Manager values.
* Set a non-default, rotated JWT secret.
* Use HTTPS for browser, API, GitHub, provider, and runner traffic.
* Restrict database credentials to the required schema operations.
* Configure private object storage and retention.
* Set provider and GitHub quotas.
* Use Redis for shared rate limiting.
* Deploy the runner independently with no host Docker socket.
* Enable logs, metrics, error alerts, and backup verification.
* Test rollback and migration recovery before the event.
* Define an incident contact and participant support process.

## Appendix E: Suggested Diagrams

### E.1 Authentication sequence

```text
Browser        API             Security module       Store
   |             |                    |                |
   |--login----->|                    |                |
   |             |--verify password->|                |
   |             |                    |--read user---->|
   |             |                    |<--hash----------|
   |             |<--create JWT-------|                |
   |<--token-----|                    |                |
   |--Bearer request----------------->|                |
   |             |--decode/check----->|                |
   |<--protected response-------------|                |
```

### E.2 Evaluation fallback sequence

```text
Judge -> API -> Evaluation service -> Configured provider
                         |                  |
                         |<--valid result--|
                         |
                         |--invalid/error--> Demo fallback
                         |
Judge <- overall score, criteria, reasons, model_mode
```

### E.3 Runner boundary

```text
API container --structured HTTPS request--> Runner service
                                                |
                                  fixed language toolchain
                                  read-only source input
                                  temporary workspace
                                  CPU/memory/time/process limits
                                                |
                                      per-test result only
```

These diagrams can be redrawn in draw.io, Lucidchart, or any institution-
approved diagram tool. The final report should label every external dependency,
trust boundary, and persistent data store.

## Appendix F: Glossary

**API:** Application Programming Interface through which software components
exchange requests and responses.  
**Artifact:** A file, link, or evidence item associated with a submission.  
**Audit event:** A record of an important action by an authenticated actor.  
**Bearer token:** A token presented in an HTTP authorization header.  
**Fallback:** A known alternative used when an optional provider fails.  
**Hackathon:** A time-limited event in which teams build and present projects.  
**JWT:** JSON Web Token containing signed claims such as subject and role.  
**MVP:** Minimum Viable Product, a limited but demonstrable product version.  
**Provider:** An external AI or data service called through an adapter.  
**Rubric:** Criteria and weights used to assess a project.  
**Sandbox:** A restricted environment for running untrusted code.  
**Signal:** Evidence that contributes to review; it is not necessarily proof.  
**Submission:** A team's project entry for a particular hackathon.  
**Webhook:** An HTTP callback used to notify another service of an event.  

## Appendix G: Final Submission Materials

The final college submission package should contain the report, source
repository link, installation instructions, database migration, screenshots,
test output, and a short demonstration video if required by the institution.
The report should not include passwords, API keys, access tokens, private
repository contents, or personal data that is not needed for evaluation.

Recommended screenshots include the repository tree, backend API documentation,
frontend dashboard, test output, and Docker or cloud service status. Screenshots
should include captions and a sentence explaining what the reviewer should
observe. A screenshot is supporting evidence; it does not replace a source
file, test command, or reproducible setup instruction.

Before printing, the author should update the report date, contributors,
supervisor, institution, tested versions, deployment URL if public, and
repository commit identifier. The implementation and report must be reviewed
together so that a planned feature is not accidentally presented as complete.
