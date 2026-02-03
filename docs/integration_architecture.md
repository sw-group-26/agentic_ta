# Agentic TA - Integration Architecture

## Overview

This document describes how the Agentic TA system integrates with iCollege (Brightspace D2L) at Georgia State University. The integration uses the LTI 1.3 standard to embed an AI-powered grading panel within the existing submissions interface.

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   USER LAYER                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐              │
│  │   Instructor    │    │       TA        │    │    Student      │              │
│  │   (Full Access) │    │ (Grading Access)│    │ (View Feedback) │              │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘              │
└───────────┼──────────────────────┼──────────────────────┼───────────────────────┘
            │                      │                      │
            └──────────────────────┼──────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                        iCollege (Brightspace D2L)                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                      Submissions Page                               │  │  │
│  │  │  ┌─────────────────────┐    ┌─────────────────────────────────┐    │  │  │
│  │  │  │  Student List       │    │   Agentic TA Panel (LTI Tool)  │    │  │  │
│  │  │  │  (Native D2L)       │    │   ┌─────────────────────────┐  │    │  │  │
│  │  │  │                     │    │   │ • Quick Actions         │  │    │  │  │
│  │  │  │  • Submission list  │◄──►│   │ • Code Viewer           │  │    │  │  │
│  │  │  │  • File downloads   │    │   │ • Test Results          │  │    │  │  │
│  │  │  │  • Grade entry      │    │   │ • AI Feedback           │  │    │  │  │
│  │  │  │                     │    │   │ • Analytics             │  │    │  │  │
│  │  │  └─────────────────────┘    │   └─────────────────────────┘  │    │  │  │
│  │  │                             └─────────────────────────────────┘    │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ LTI 1.3 / OAuth 2.0
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               API GATEWAY LAYER                                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         Agentic TA API Gateway                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │    Auth      │  │   Rate       │  │   Request    │  │    Load      │  │  │
│  │  │  Middleware  │  │   Limiter    │  │   Validator  │  │   Balancer   │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                        Agentic TA Microservices                             ││
│  │                                                                              ││
│  │  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐        ││
│  │  │  Grading Service │   │ Feedback Service │   │ Analytics Service│        ││
│  │  │  ─────────────── │   │  ─────────────── │   │  ─────────────── │        ││
│  │  │  • Score calc    │   │  • LLM interface │   │  • Metrics       │        ││
│  │  │  • Test runner   │   │  • Template mgmt │   │  • Dashboards    │        ││
│  │  │  • Rubric eval   │   │  • Tone analysis │   │  • At-risk flags │        ││
│  │  └────────┬─────────┘   └────────┬─────────┘   └────────┬─────────┘        ││
│  │           │                      │                      │                   ││
│  │  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐        ││
│  │  │Plagiarism Service│   │   OCR Service    │   │ Execution Service│        ││
│  │  │  ─────────────── │   │  ─────────────── │   │  ─────────────── │        ││
│  │  │  • Code compare  │   │  • Image process │   │  • Docker sandbox│        ││
│  │  │  • Historical DB │   │  • Text extract  │   │  • Multi-language│        ││
│  │  │  • Similarity %  │   │  • Handwriting   │   │  • Resource limit│        ││
│  │  └──────────────────┘   └──────────────────┘   └──────────────────┘        ││
│  │                                                                              ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL SERVICES LAYER                               │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐             │
│  │    LLM Provider  │   │   OCR Provider   │   │  Code Execution  │             │
│  │  ─────────────── │   │  ─────────────── │   │  ─────────────── │             │
│  │  • OpenAI GPT-4  │   │  • Google Vision │   │  • Docker Engine │             │
│  │  • Claude API    │   │  • AWS Textract  │   │  • Judge0 API    │             │
│  │  • Local LLM     │   │  • Tesseract     │   │  • Custom runner │             │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                DATA LAYER                                        │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐             │
│  │    PostgreSQL    │   │     MongoDB      │   │      Redis       │             │
│  │  ─────────────── │   │  ─────────────── │   │  ─────────────── │             │
│  │  • Users         │   │  • Submissions   │   │  • Session cache │             │
│  │  • Courses       │   │  • Code files    │   │  • Rate limiting │             │
│  │  • Grades        │   │  • Feedback docs │   │  • Job queue     │             │
│  │  • Analytics     │   │  • Historical DB │   │  • Real-time pub │             │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### 1. LTI 1.3 Integration with iCollege

The Agentic TA integrates with iCollege using the Learning Tools Interoperability (LTI) 1.3 standard.

```
┌─────────────────────────────────────────────────────────────────┐
│                    LTI 1.3 Launch Flow                          │
└─────────────────────────────────────────────────────────────────┘

    Instructor/TA                    iCollege                  Agentic TA
         │                              │                           │
         │  1. Click Agentic TA button  │                           │
         │─────────────────────────────>│                           │
         │                              │                           │
         │                              │  2. Generate LTI message  │
         │                              │   (JWT with claims)       │
         │                              │──────────────────────────>│
         │                              │                           │
         │                              │  3. Validate JWT          │
         │                              │   - Check signature       │
         │                              │   - Verify claims         │
         │                              │   - Extract user info     │
         │                              │<──────────────────────────│
         │                              │                           │
         │  4. Return Agentic TA Panel  │  5. Load panel iframe     │
         │<─────────────────────────────│<──────────────────────────│
         │                              │                           │
```

**LTI Claims Used:**
- `sub`: User ID
- `name`: User display name
- `email`: User email
- `roles`: LTI role (Instructor, TeachingAssistant)
- `context_id`: Course ID
- `resource_link_id`: Assignment ID
- Custom claims for submission data

### 2. Data Exchange with D2L

```
┌─────────────────────────────────────────────────────────────────┐
│                  Data Exchange Architecture                      │
└─────────────────────────────────────────────────────────────────┘

                     Agentic TA Backend
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌───────────────┐ ┌───────────┐ ┌───────────────┐
    │ D2L Grades API│ │ D2L Files │ │ D2L Users API │
    │               │ │    API    │ │               │
    └───────────────┘ └───────────┘ └───────────────┘
            │               │               │
            │  REST/OAuth   │               │
            └───────────────┴───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    iCollege   │
                    │   Database    │
                    └───────────────┘
```

**API Endpoints Used:**

| D2L API | Purpose |
|---------|---------|
| `/d2l/api/le/{version}/{orgUnitId}/dropbox/folders/{folderId}/submissions/` | Get submissions |
| `/d2l/api/le/{version}/{orgUnitId}/dropbox/folders/{folderId}/submissions/{submissionId}/files/{fileId}` | Download files |
| `/d2l/api/le/{version}/{orgUnitId}/grades/` | Post grades |
| `/d2l/api/le/{version}/{orgUnitId}/grades/{gradeObjectId}/values/{userId}` | Update grade |

---

## Component Details

### 1. Grading Service

Handles automated code evaluation.

```
┌────────────────────────────────────────────────────────────┐
│                    Grading Service Flow                     │
└────────────────────────────────────────────────────────────┘

    Submission              Grading Service              Result
        │                         │                        │
        │  1. Upload submission   │                        │
        │────────────────────────>│                        │
        │                         │                        │
        │                   ┌─────┴─────┐                  │
        │                   │ Extract   │                  │
        │                   │  Files    │                  │
        │                   └─────┬─────┘                  │
        │                         │                        │
        │                   ┌─────┴─────┐                  │
        │                   │  Detect   │                  │
        │                   │ Language  │                  │
        │                   └─────┬─────┘                  │
        │                         │                        │
        │                   ┌─────┴─────┐                  │
        │                   │   Run     │                  │
        │                   │  Tests    │◄─── Docker Sandbox
        │                   └─────┬─────┘                  │
        │                         │                        │
        │                   ┌─────┴─────┐                  │
        │                   │  Apply    │                  │
        │                   │  Rubric   │                  │
        │                   └─────┬─────┘                  │
        │                         │                        │
        │                         │  2. Return results     │
        │                         │───────────────────────>│
        │                         │                        │
```

### 2. Feedback Service

Generates personalized AI feedback.

```
┌────────────────────────────────────────────────────────────┐
│                   Feedback Generation Flow                  │
└────────────────────────────────────────────────────────────┘

    Inputs                    LLM Processing                Output
    ─────                     ──────────────                ──────

    ┌──────────────┐
    │ Student Code │──┐
    └──────────────┘  │
                      │    ┌─────────────────────────┐
    ┌──────────────┐  │    │                         │
    │ Test Results │──┼───>│    Prompt Engineering   │
    └──────────────┘  │    │                         │
                      │    │  • Code analysis        │    ┌──────────────┐
    ┌──────────────┐  │    │  • Error explanation    │───>│  Structured  │
    │   Rubric     │──┼───>│  • Style feedback       │    │   Feedback   │
    └──────────────┘  │    │  • Improvement tips     │    └──────────────┘
                      │    │                         │
    ┌──────────────┐  │    └─────────────────────────┘
    │  Context     │──┘              │
    │ (past work)  │                 │
    └──────────────┘                 ▼
                            ┌─────────────────┐
                            │   LLM API       │
                            │  (GPT-4/Claude) │
                            └─────────────────┘
```

### 3. Code Execution Service

Sandboxed environment for running student code.

```
┌────────────────────────────────────────────────────────────┐
│                Code Execution Architecture                  │
└────────────────────────────────────────────────────────────┘

                        Execution Service
                              │
                    ┌─────────┴─────────┐
                    │   Job Queue       │
                    │   (Redis)         │
                    └─────────┬─────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │   Worker 1    │ │   Worker 2    │ │   Worker N    │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                 │                 │
            ▼                 ▼                 ▼
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │    Docker     │ │    Docker     │ │    Docker     │
    │   Container   │ │   Container   │ │   Container   │
    │               │ │               │ │               │
    │ • No network  │ │ • CPU limit   │ │ • Mem limit   │
    │ • Read-only   │ │ • Time limit  │ │ • Disk limit  │
    │ • Isolated    │ │               │ │               │
    └───────────────┘ └───────────────┘ └───────────────┘
```

**Security Measures:**
- Network isolation (no outbound connections)
- Read-only filesystem with temp workspace
- CPU time limit (30 seconds default)
- Memory limit (512MB default)
- Process limit (10 processes max)
- No privileged operations

---

## UI Integration Points

### Where Agentic TA Appears in iCollege

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         iCollege Navigation                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Content | Collaboration | Assessments | Grades | Classlist | Course Tools  │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Assessments Dropdown                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Assignments  ◄────── Entry point 1                                        │
│  • Quizzes                                                                   │
│  • Rubrics                                                                   │
│  • Agentic TA Settings  ◄────── Entry point 2 (Instructor only)             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Assignments → lab1 → Submissions                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────┐  ┌─────────────────────────────────┐│
│  │                                    │  │                                 ││
│  │      Existing Submissions List     │  │      AGENTIC TA PANEL          ││
│  │                                    │  │      (LTI Embedded)             ││
│  │      • Student name               │  │                                 ││
│  │      • Submission date            │  │      Appears as collapsible     ││
│  │      • Files                      │  │      sidebar on right side      ││
│  │      • Actions                    │  │                                 ││
│  │                                    │  │      • Grading controls         ││
│  │                                    │  │      • AI feedback              ││
│  │                                    │  │      • Code viewer              ││
│  │                                    │  │      • Test results             ││
│  │                                    │  │                                 ││
│  └────────────────────────────────────┘  └─────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Complete Data Flow                                   │
└─────────────────────────────────────────────────────────────────────────────┘

    TA/Instructor
         │
         │ 1. Select submission to grade
         ▼
    ┌─────────────┐     2. Fetch files      ┌─────────────┐
    │  Agentic TA │────────────────────────>│   iCollege  │
    │    Panel    │<────────────────────────│   D2L API   │
    └─────────────┘     3. Return files     └─────────────┘
         │
         │ 4. Send for grading
         ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                     Agentic TA Backend                               │
    │                                                                      │
    │  5. Extract    6. Execute     7. Run         8. Check      9. Get   │
    │     files         code        tests       plagiarism    feedback    │
    │      │             │            │              │             │       │
    │      ▼             ▼            ▼              ▼             ▼       │
    │  ┌───────┐    ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌─────────┐  │
    │  │Extract│    │ Docker  │  │  Test   │  │Historical│  │   LLM   │  │
    │  │Service│    │ Sandbox │  │ Runner  │  │    DB    │  │   API   │  │
    │  └───────┘    └─────────┘  └─────────┘  └──────────┘  └─────────┘  │
    │                                                                      │
    └─────────────────────────────────────────────────────────────────────┘
         │
         │ 10. Return grading results
         ▼
    ┌─────────────┐
    │  Agentic TA │  11. TA reviews/edits feedback
    │    Panel    │
    └─────────────┘
         │
         │ 12. Publish grades
         ▼
    ┌─────────────┐     13. Post grade      ┌─────────────┐
    │  Agentic TA │────────────────────────>│   iCollege  │
    │   Backend   │                          │  Grade API  │
    └─────────────┘                          └─────────────┘
         │
         │ 14. Store for analytics
         ▼
    ┌─────────────┐
    │  Analytics  │
    │   Database  │
    └─────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Security Layers                                      │
└─────────────────────────────────────────────────────────────────────────────┘

    Internet
        │
        ▼
    ┌───────────────────────────────────────────────────────┐
    │                   WAF / DDoS Protection                │
    │                   (Cloudflare / AWS WAF)               │
    └───────────────────────────────────────────────────────┘
        │
        ▼
    ┌───────────────────────────────────────────────────────┐
    │                   TLS 1.3 Termination                  │
    │                   (All traffic encrypted)              │
    └───────────────────────────────────────────────────────┘
        │
        ▼
    ┌───────────────────────────────────────────────────────┐
    │                   API Gateway                          │
    │   • JWT validation                                     │
    │   • Rate limiting (100 req/min per user)              │
    │   • Request validation                                 │
    │   • Audit logging                                      │
    └───────────────────────────────────────────────────────┘
        │
        ▼
    ┌───────────────────────────────────────────────────────┐
    │                   Application Layer                    │
    │   • Role-based access control (RBAC)                  │
    │   • Input sanitization                                 │
    │   • SQL injection prevention                           │
    │   • XSS prevention                                     │
    └───────────────────────────────────────────────────────┘
        │
        ▼
    ┌───────────────────────────────────────────────────────┐
    │                   Data Layer                           │
    │   • Encryption at rest (AES-256)                      │
    │   • Database access controls                          │
    │   • PII minimization                                   │
    │   • Audit trails                                       │
    └───────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Cloud Deployment (AWS Example)                            │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                              VPC                                         │
    │  ┌───────────────────────────────────────────────────────────────────┐  │
    │  │                        Public Subnet                               │  │
    │  │  ┌─────────────────┐    ┌─────────────────┐                       │  │
    │  │  │   ALB           │    │   NAT Gateway   │                       │  │
    │  │  │ (Load Balancer) │    │                 │                       │  │
    │  │  └────────┬────────┘    └─────────────────┘                       │  │
    │  └───────────┼───────────────────────────────────────────────────────┘  │
    │              │                                                           │
    │  ┌───────────┼───────────────────────────────────────────────────────┐  │
    │  │           │              Private Subnet                            │  │
    │  │           ▼                                                        │  │
    │  │  ┌─────────────────────────────────────────────────────────────┐  │  │
    │  │  │                     ECS Cluster                              │  │  │
    │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │  │  │
    │  │  │  │ API      │  │ Grading  │  │ Feedback │  │Analytics │    │  │  │
    │  │  │  │ Service  │  │ Service  │  │ Service  │  │ Service  │    │  │  │
    │  │  │  │ (3x)     │  │ (5x)     │  │ (3x)     │  │ (2x)     │    │  │  │
    │  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │  │  │
    │  │  └─────────────────────────────────────────────────────────────┘  │  │
    │  │                                                                    │  │
    │  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │  │
    │  │  │   RDS            │  │   DocumentDB     │  │   ElastiCache    │ │  │
    │  │  │   (PostgreSQL)   │  │   (MongoDB)      │  │   (Redis)        │ │  │
    │  │  └──────────────────┘  └──────────────────┘  └──────────────────┘ │  │
    │  └───────────────────────────────────────────────────────────────────┘  │
    └─────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React, TypeScript | Panel UI |
| **API Gateway** | Kong / AWS API Gateway | Auth, rate limiting |
| **Backend Services** | Python (FastAPI) | Microservices |
| **LLM Integration** | OpenAI/Anthropic API | Feedback generation |
| **Code Execution** | Docker, Judge0 | Sandboxed execution |
| **Databases** | PostgreSQL, MongoDB, Redis | Data storage |
| **Message Queue** | RabbitMQ / Redis Streams | Async processing |
| **Monitoring** | Prometheus, Grafana | Observability |
| **CI/CD** | GitHub Actions, ArgoCD | Deployment |
| **Cloud** | AWS / GCP / Azure | Infrastructure |

---

## Mockup Files Reference

The following HTML mockups demonstrate the UI integration:

1. **`mockups/icollege_integration.html`** - Main integration showing the Agentic TA panel embedded in the iCollege submissions page
2. **`mockups/analytics_dashboard.html`** - Standalone analytics view for course-wide insights
3. **`mockups/batch_grading.html`** - Batch grading interface for processing multiple submissions

Open these files in a browser to see the interactive mockups.

---

**Document Version:** 1.0
**Last Updated:** January 26, 2026
