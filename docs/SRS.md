# Software Requirements Specification (SRS)
## Agentic TA - Intelligent Grading Assistant for Computer Science Courses

**Version:** 1.0
**Date:** January 26, 2026
**Project:** Agentic TA for iCollege Integration
**Institution:** Georgia State University

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [System Features and Requirements](#3-system-features-and-requirements)
4. [External Interface Requirements](#4-external-interface-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Data Requirements](#6-data-requirements)
7. [Appendices](#7-appendices)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document describes the functional and non-functional requirements for the **Agentic TA** system - an AI-powered teaching assistant designed to automate and enhance the grading process for computer science courses at Georgia State University. The system will integrate with iCollege (Brightspace D2L) to provide intelligent feedback, automated code evaluation, and analytics for instructors and teaching assistants.

### 1.2 Scope

The Agentic TA system will:

- Integrate as a supplementary panel within the iCollege submissions page
- Provide automated grading for programming assignments
- Generate personalized, constructive feedback for students
- Execute and test student code in a sandboxed environment
- Detect potential plagiarism by comparing submissions across current and historical offerings
- Support OCR for handwritten assignment components
- Flag under-performing students for early intervention
- Maintain context from previous course offerings for consistent grading

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| **Agentic TA** | The AI-powered teaching assistant system |
| **iCollege** | Georgia State University's Learning Management System (Brightspace D2L) |
| **LLM** | Large Language Model |
| **OCR** | Optical Character Recognition |
| **TA** | Teaching Assistant |
| **SRS** | Software Requirements Specification |
| **API** | Application Programming Interface |
| **LTI** | Learning Tools Interoperability |
| **IDE** | Integrated Development Environment |

### 1.4 References

- Brightspace D2L LTI Integration Documentation
- OWASP Security Guidelines
- FERPA Compliance Requirements for Educational Software

### 1.5 Overview

This document is organized into sections covering the system description, functional requirements, interface specifications, and non-functional requirements. It serves as the primary reference for development, testing, and validation of the Agentic TA system.

---

## 2. Overall Description

### 2.1 Product Perspective

The Agentic TA operates as an embedded tool within the existing iCollege ecosystem. It extends the functionality of the Assignments/Submissions page by adding an AI-powered grading panel accessible only to instructors and teaching assistants.

```
┌─────────────────────────────────────────────────────────────────┐
│                         iCollege (D2L)                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Submissions Page (Existing)                │    │
│  │  ┌─────────────────────┐  ┌─────────────────────────┐   │    │
│  │  │   Student List      │  │   Agentic TA Panel     │   │    │
│  │  │   (Existing)        │  │   (NEW INTEGRATION)    │   │    │
│  │  │                     │  │                         │   │    │
│  │  │   • James Rawat     │  │   • AI Grading         │   │    │
│  │  │   • Varun Currie    │  │   • Feedback Gen       │   │    │
│  │  │   • ...             │  │   • Code Execution     │   │    │
│  │  │                     │  │   • Analytics          │   │    │
│  │  └─────────────────────┘  └─────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Product Functions

| Function Category | Description |
|-------------------|-------------|
| **Automated Grading** | Evaluate code submissions against rubrics and test cases |
| **Feedback Generation** | Produce personalized, constructive feedback using LLM |
| **Code Execution** | Run student code in sandboxed environment |
| **Plagiarism Detection** | Compare submissions against historical database |
| **OCR Processing** | Extract text from handwritten components |
| **Student Analytics** | Track performance and flag at-risk students |
| **Batch Processing** | Grade multiple submissions simultaneously |

### 2.3 User Classes and Characteristics

| User Class | Description | Access Level |
|------------|-------------|--------------|
| **Instructor** | Course professor with full administrative access | Full access to all features, configuration, and analytics |
| **Teaching Assistant (TA)** | Graduate/undergraduate assistants helping with grading | Access to grading, feedback, and student-level analytics |
| **System Administrator** | IT staff managing iCollege integration | Configuration and maintenance access |

**Note:** Students do NOT have access to the Agentic TA interface. They only receive the published feedback through the standard iCollege feedback mechanism.

### 2.4 Operating Environment

- **Platform:** Web-based, integrated with iCollege (Brightspace D2L)
- **Browser Support:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Backend:** Cloud-hosted services (AWS/GCP/Azure)
- **LLM Provider:** OpenAI GPT-4 / Anthropic Claude / Open-source alternatives
- **Database:** PostgreSQL for relational data, MongoDB for submission artifacts

### 2.5 Design and Implementation Constraints

1. Must comply with FERPA regulations for student data privacy
2. Must integrate via LTI 1.3 standard for iCollege compatibility
3. Code execution must be sandboxed to prevent security breaches
4. Must handle concurrent grading requests for classes up to 500 students
5. Response time for single submission grading should not exceed 60 seconds

### 2.6 Assumptions and Dependencies

**Assumptions:**
- iCollege supports LTI 1.3 tool integration
- Instructors will provide rubrics and test cases for assignments
- Internet connectivity is available for LLM API calls

**Dependencies:**
- Brightspace D2L LTI API availability
- LLM provider API availability and rate limits
- University IT approval for third-party integration

---

## 3. System Features and Requirements

### 3.1 Automated Code Grading

#### 3.1.1 Description
The system shall automatically evaluate programming assignments by executing code, running test cases, and applying rubric criteria.

#### 3.1.2 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | System shall extract submitted code files from zip archives | High |
| FR-1.2 | System shall detect programming language from file extensions | High |
| FR-1.3 | System shall execute code in sandboxed Docker containers | High |
| FR-1.4 | System shall run instructor-provided test cases against submissions | High |
| FR-1.5 | System shall compute scores based on test case results and rubric | High |
| FR-1.6 | System shall handle compilation/runtime errors gracefully | High |
| FR-1.7 | System shall support Python, Java, C, C++, and JavaScript | Medium |
| FR-1.8 | System shall enforce execution time limits (30 seconds default) | High |
| FR-1.9 | System shall enforce memory limits (512MB default) | High |

### 3.2 AI-Powered Feedback Generation

#### 3.2.1 Description
The system shall generate personalized, constructive feedback using Large Language Models.

#### 3.2.2 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | System shall analyze code quality (style, structure, efficiency) | High |
| FR-2.2 | System shall generate feedback specific to identified issues | High |
| FR-2.3 | System shall provide suggestions for improvement | High |
| FR-2.4 | System shall maintain constructive and encouraging tone | High |
| FR-2.5 | System shall reference specific line numbers in feedback | Medium |
| FR-2.6 | System shall allow TA to edit generated feedback before publishing | High |
| FR-2.7 | System shall learn from TA edits to improve future feedback | Low |
| FR-2.8 | System shall support feedback templates configurable by instructor | Medium |

### 3.3 Plagiarism Detection

#### 3.3.1 Description
The system shall detect potential plagiarism by comparing submissions against current classmates and historical submissions.

#### 3.3.2 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | System shall compute code similarity scores between submissions | High |
| FR-3.2 | System shall compare against historical submissions from past semesters | High |
| FR-3.3 | System shall flag submissions exceeding similarity threshold | High |
| FR-3.4 | System shall display side-by-side comparison for flagged submissions | Medium |
| FR-3.5 | System shall exclude instructor-provided starter code from comparison | High |
| FR-3.6 | System shall generate plagiarism report with confidence scores | Medium |

### 3.4 OCR for Handwritten Components

#### 3.4.1 Description
The system shall extract text from handwritten assignment components (e.g., algorithm explanations, pseudocode).

#### 3.4.2 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | System shall accept image uploads (PNG, JPG, PDF) | Medium |
| FR-4.2 | System shall extract text using OCR technology | Medium |
| FR-4.3 | System shall display extracted text alongside original image | Medium |
| FR-4.4 | System shall allow TA to correct OCR errors | Medium |

### 3.5 Student Performance Analytics

#### 3.5.1 Description
The system shall track student performance and flag at-risk students for early intervention.

#### 3.5.2 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | System shall track submission history per student | Medium |
| FR-5.2 | System shall compute performance trends across assignments | Medium |
| FR-5.3 | System shall flag students with declining performance | High |
| FR-5.4 | System shall flag students with multiple late/missing submissions | High |
| FR-5.5 | System shall generate class-wide analytics dashboard | Medium |
| FR-5.6 | System shall send notification alerts for flagged students | Medium |

### 3.6 Rubric and Answer Key Configuration

#### 3.6.1 Description
The system shall allow TAs and instructors to configure grading rubrics and upload answer keys/solutions that the AI will use as reference for automated grading.

#### 3.6.2 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-6.1 | System shall provide interface to create/edit grading rubrics | High |
| FR-6.2 | System shall support rubric categories with point allocations | High |
| FR-6.3 | System shall allow upload of solution/answer key files | High |
| FR-6.4 | System shall allow upload of reference test cases | High |
| FR-6.5 | System shall support multiple solution variants (alternative correct answers) | Medium |
| FR-6.6 | System shall store rubrics for reuse in future semesters | Medium |
| FR-6.7 | System shall allow import/export of rubrics in standard formats | Low |
| FR-6.8 | System shall support partial credit rules per rubric item | High |
| FR-6.9 | System shall allow weighting of different rubric categories | High |
| FR-6.10 | System shall validate uploaded answer keys by running test cases | Medium |

### 3.7 Batch Grading Operations

#### 3.7.1 Description
The system shall support grading multiple submissions (50+ students) in a single session without leaving iCollege, with mandatory manual review and approval before grades are published.

#### 3.7.2 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-7.1 | System shall allow selection of multiple submissions for batch grading | High |
| FR-7.2 | System shall support "Grade All Ungraded" action for entire class | High |
| FR-7.3 | System shall process batch grading without requiring page navigation | High |
| FR-7.4 | System shall display real-time progress indicator during batch operations | High |
| FR-7.5 | System shall queue batch operations to manage system load | Medium |
| FR-7.6 | System shall allow pause/resume of batch grading operations | Medium |
| FR-7.7 | System shall handle 50+ submissions in a single batch session | High |
| FR-7.8 | System shall maintain grading state if browser connection is interrupted | Medium |

### 3.8 Manual Review and Approval Workflow

#### 3.8.1 Description
The system shall require TAs/instructors to manually review and approve all AI-generated grades and feedback before they are published to students.

#### 3.8.2 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-8.1 | System shall NOT automatically publish any grades without TA approval | High |
| FR-8.2 | System shall present each graded submission for TA review | High |
| FR-8.3 | System shall allow TA to approve, reject, or modify AI-generated grades | High |
| FR-8.4 | System shall allow TA to edit AI-generated feedback before approval | High |
| FR-8.5 | System shall provide "Approve All" option for bulk approval (with confirmation) | Medium |
| FR-8.6 | System shall highlight submissions requiring attention (low confidence, flagged) | High |
| FR-8.7 | System shall track approval status: Pending Review, Approved, Published | High |
| FR-8.8 | System shall require explicit "Publish" action to release grades to students | High |
| FR-8.9 | System shall allow selective publishing (publish some, hold others) | Medium |
| FR-8.10 | System shall maintain audit trail of all approvals and modifications | High |
| FR-8.11 | System shall show side-by-side comparison of AI grade vs TA modified grade | Medium |
| FR-8.12 | System shall allow TA to add private notes (not visible to students) | Low |

### 3.9 Integrated Code Environment

#### 3.9.1 Description
The system shall provide an embedded code viewer/editor for reviewing submissions.

#### 3.9.2 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-9.1 | System shall display submitted code with syntax highlighting | High |
| FR-9.2 | System shall show line numbers and support code folding | Medium |
| FR-9.3 | System shall allow inline comments/annotations by TA | Medium |
| FR-9.4 | System shall provide "Run Code" button to execute in sandbox | High |
| FR-9.5 | System shall display execution output and error messages | High |
| FR-9.6 | System shall show diff view comparing student code to solution | Medium |

---

## 4. External Interface Requirements

### 4.1 User Interfaces

#### 4.1.1 Main Integration Panel

The Agentic TA panel shall appear as a collapsible sidebar on the right side of the iCollege Submissions page.

**Panel Components:**
1. **Header Bar** - Agentic TA branding, collapse/expand toggle
2. **Quick Actions** - Grade Selected, Grade All, View Analytics
3. **Grading Queue** - List of submissions pending review
4. **Active Grading View** - Currently selected submission details
5. **Feedback Editor** - AI-generated feedback with edit capability
6. **Analytics Summary** - Class performance overview

#### 4.1.2 UI State Diagram

```
┌─────────────┐    Select      ┌─────────────┐
│   Closed    │ ───────────►   │   Open      │
│   Panel     │                │   Panel     │
└─────────────┘  ◄───────────  └─────────────┘
                   Collapse            │
                                       │ Select Submission
                                       ▼
                               ┌─────────────┐
                               │  Grading    │
                               │   View      │
                               └─────────────┘
                                       │
                        ┌──────────────┼──────────────┐
                        ▼              ▼              ▼
                 ┌──────────┐  ┌──────────┐  ┌──────────┐
                 │ Run Code │  │ Generate │  │  View    │
                 │          │  │ Feedback │  │ Similarity│
                 └──────────┘  └──────────┘  └──────────┘
```

### 4.2 Hardware Interfaces

Not applicable - the system is entirely web-based.

### 4.3 Software Interfaces

| Interface | Protocol | Description |
|-----------|----------|-------------|
| iCollege (D2L) | LTI 1.3 | Integration with LMS for submission access |
| LLM Provider | REST API | Feedback generation and code analysis |
| Code Execution | Docker API | Sandboxed code execution |
| Database | PostgreSQL/MongoDB | Data persistence |
| OCR Service | REST API | Text extraction from images |

### 4.4 Communication Interfaces

- **HTTPS:** All communications encrypted via TLS 1.3
- **WebSocket:** Real-time updates for batch grading progress
- **OAuth 2.0:** Authentication with iCollege

---

## 5. Non-Functional Requirements

### 5.1 Performance Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Single submission grading response time | < 60 seconds |
| NFR-1.2 | Batch grading throughput | 50 submissions/minute |
| NFR-1.3 | UI panel load time | < 2 seconds |
| NFR-1.4 | Code execution timeout | Configurable, default 30s |
| NFR-1.5 | Concurrent users supported | 100 |

### 5.2 Security Requirements

| ID | Requirement |
|----|-------------|
| NFR-2.1 | All student data must be encrypted at rest (AES-256) |
| NFR-2.2 | All communications must use TLS 1.3 |
| NFR-2.3 | Code execution must be fully sandboxed (no network, limited fs) |
| NFR-2.4 | Access control must enforce role-based permissions |
| NFR-2.5 | Audit logs must be maintained for all grading actions |
| NFR-2.6 | System must comply with FERPA regulations |

### 5.3 Reliability Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-3.1 | System uptime | 99.5% |
| NFR-3.2 | Data backup frequency | Daily |
| NFR-3.3 | Recovery time objective (RTO) | 4 hours |
| NFR-3.4 | Recovery point objective (RPO) | 1 hour |

### 5.4 Usability Requirements

| ID | Requirement |
|----|-------------|
| NFR-4.1 | Interface must be consistent with iCollege design language |
| NFR-4.2 | All actions must provide visual feedback within 200ms |
| NFR-4.3 | Error messages must be clear and actionable |
| NFR-4.4 | System must support keyboard navigation |
| NFR-4.5 | System must meet WCAG 2.1 AA accessibility standards |

### 5.5 Scalability Requirements

| ID | Requirement |
|----|-------------|
| NFR-5.1 | System must support courses with up to 500 students |
| NFR-5.2 | System must handle end-of-semester grading surge (10x normal load) |
| NFR-5.3 | Database must support 5 years of historical submission data |

---

## 6. Data Requirements

### 6.1 Data Models

#### 6.1.1 Core Entities

```
┌─────────────────┐       ┌─────────────────┐
│     Course      │       │   Assignment    │
├─────────────────┤       ├─────────────────┤
│ course_id (PK)  │──────<│ assignment_id   │
│ name            │       │ course_id (FK)  │
│ semester        │       │ title           │
│ instructor_id   │       │ due_date        │
│ created_at      │       │ rubric          │
└─────────────────┘       │ test_cases      │
                          └─────────────────┘
                                  │
                                  │
                          ┌───────▼─────────┐
                          │   Submission    │
                          ├─────────────────┤
                          │ submission_id   │
                          │ assignment_id   │
                          │ student_id      │
                          │ submitted_at    │
                          │ file_path       │
                          │ status          │
                          └─────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
┌────────▼────────┐    ┌─────────▼─────────┐    ┌────────▼────────┐
│  GradingResult  │    │     Feedback      │    │ SimilarityScore │
├─────────────────┤    ├───────────────────┤    ├─────────────────┤
│ result_id       │    │ feedback_id       │    │ score_id        │
│ submission_id   │    │ submission_id     │    │ submission_id   │
│ score           │    │ ai_generated      │    │ compared_to_id  │
│ test_results    │    │ ta_edited         │    │ similarity_pct  │
│ graded_by       │    │ final_text        │    │ flagged         │
│ graded_at       │    │ created_at        │    └─────────────────┘
└─────────────────┘    └───────────────────┘
```

### 6.2 Data Retention

| Data Type | Retention Period |
|-----------|------------------|
| Submissions | 5 years (for plagiarism detection) |
| Grading Results | 5 years |
| Feedback | 5 years |
| Audit Logs | 7 years |
| Analytics Data | 3 years |

### 6.3 Data Privacy

- Student personally identifiable information (PII) must be minimized
- Data access must be logged for FERPA compliance
- Students have right to request their data under FERPA

---

## 7. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| Brightspace D2L | Learning Management System platform used by iCollege |
| Docker | Containerization platform for sandboxed execution |
| FERPA | Family Educational Rights and Privacy Act |
| LTI | Learning Tools Interoperability - standard for LMS integration |
| Rubric | Grading criteria and point allocation for assignments |
| Sandbox | Isolated execution environment for security |

### Appendix B: Use Case Diagrams

```
                    ┌─────────────────────────────────────┐
                    │           Agentic TA System         │
                    │                                     │
    ┌───────┐       │   ┌─────────────────────────┐      │
    │       │       │   │    Grade Submission     │      │
    │  TA   │───────┼──►│                         │      │
    │       │       │   └─────────────────────────┘      │
    └───────┘       │                                     │
        │          │   ┌─────────────────────────┐      │
        │          │   │   Review AI Feedback    │      │
        └──────────┼──►│                         │      │
                    │   └─────────────────────────┘      │
                    │                                     │
    ┌───────┐       │   ┌─────────────────────────┐      │
    │       │       │   │   Configure Rubric      │      │
    │Instrctr│──────┼──►│                         │      │
    │       │       │   └─────────────────────────┘      │
    └───────┘       │                                     │
        │          │   ┌─────────────────────────┐      │
        │          │   │   View Analytics        │      │
        └──────────┼──►│                         │      │
                    │   └─────────────────────────────┘      │
                    │                                     │
                    │   ┌─────────────────────────┐      │
                    │   │   Detect Plagiarism     │      │
                    │   │                         │◄─────┤
                    │   └─────────────────────────┘      │
                    │                                     │
                    └─────────────────────────────────────┘
```

### Appendix C: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-26 | Project Team | Initial version |

---

**End of Software Requirements Specification**
