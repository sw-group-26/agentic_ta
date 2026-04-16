# Agentic TA - AI-Powered Grading Assistant

An intelligent teaching assistant system designed to automate and enhance the grading process for computer science courses at Georgia State University. Integrates directly with iCollege (Brightspace D2L).

---

## Project Overview

### Problem Statement

- Grading programming assignments for large classrooms is time-consuming
- Manual feedback is inconsistent and often lacks detail
- TAs spend excessive time on repetitive evaluation tasks
- No integrated solution exists within iCollege for automated code grading

### Solution: Agentic TA

An AI-powered grading assistant that:
- Integrates directly into the iCollege submissions page
- Allows TAs to provide rubrics and answer keys
- Automatically grades 50+ submissions in one sitting
- Generates personalized, constructive feedback using LLM
- Requires manual approval before publishing grades to students
- All without leaving iCollege

### Target Users

- Teaching Assistants (TAs) in computer science courses
- Course Instructors

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Rubric Configuration** | TA defines grading criteria, point allocations, and partial credit rules |
| **Answer Key Upload** | Upload solution files and test cases for AI reference |
| **Batch Grading** | Grade 50+ submissions in a single session |
| **AI Feedback** | Generate personalized feedback using LLM (GPT-4/Claude) |
| **Manual Approval** | Review and approve all grades before publishing |
| **Code Execution** | Run student code in sandboxed environment |
| **Plagiarism Detection** | Compare against current and historical submissions |
| **OCR Support** | Extract text from handwritten components |
| **Student Analytics** | Flag under-performing students for early intervention |
| **Context Preservation** | Maintain grading context from previous course offerings |

---

## Documentation

### Requirements Specification

- **[docs/SRS.md](docs/SRS.md)** - Complete Software Requirements Specification
  - Functional requirements
  - Non-functional requirements
  - Data models
  - Use cases

### Architecture

- **[docs/integration_architecture.md](docs/integration_architecture.md)** - Integration Architecture
  - System architecture diagrams
  - LTI 1.3 integration with iCollege
  - Data flow diagrams
  - Security architecture
  - Deployment architecture

---

## UI Mockups

Interactive HTML mockups demonstrating the user interface:

| Mockup | Description | Open |
|--------|-------------|------|
| **iCollege Integration** | Main grading panel integrated into iCollege submissions page | [mockups/icollege_integration.html](mockups/icollege_integration.html) |
| **Rubric Configuration** | Interface for setting up grading rubrics and uploading answer keys | [mockups/rubric_configuration.html](mockups/rubric_configuration.html) |
| **Batch Grading** | Interface for grading multiple submissions simultaneously | [mockups/batch_grading.html](mockups/batch_grading.html) |
| **Approval Workflow** | Review and approve grades before publishing to students | [mockups/approval_workflow.html](mockups/approval_workflow.html) |
| **Analytics Dashboard** | Course-wide performance analytics and at-risk student alerts | [mockups/analytics_dashboard.html](mockups/analytics_dashboard.html) |

**To view mockups:** Open the HTML files in any web browser.

---

## iCollege Integration Points

The Agentic TA integrates into two locations within iCollege:

1. **Submissions Page** - A collapsible panel on the right side where TAs can:
   - View and grade submissions
   - Run student code
   - Generate and edit feedback
   - Approve and publish grades

2. **Assessment Settings** - Configuration page where instructors can:
   - Create/edit grading rubrics
   - Upload answer keys and test cases
   - Configure grading options

---

## Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GRADING WORKFLOW                              │
└─────────────────────────────────────────────────────────────────────┘

    1. CONFIGURE              2. GRADE                3. APPROVE & PUBLISH
    ────────────              ────────                ────────────────────

    ┌─────────────┐          ┌─────────────┐         ┌─────────────┐
    │ Upload      │          │ Select      │         │ Review AI   │
    │ Rubric      │ ───────► │ Submissions │ ──────► │ Grades      │
    └─────────────┘          └─────────────┘         └─────────────┘
          │                        │                       │
          ▼                        ▼                       ▼
    ┌─────────────┐          ┌─────────────┐         ┌─────────────┐
    │ Upload      │          │ Click       │         │ Edit        │
    │ Answer Key  │ ───────► │ "Grade All" │ ──────► │ Feedback    │
    └─────────────┘          └─────────────┘         └─────────────┘
          │                        │                       │
          ▼                        ▼                       ▼
    ┌─────────────┐          ┌─────────────┐         ┌─────────────┐
    │ Define      │          │ AI Grades   │         │ Approve &   │
    │ Test Cases  │ ───────► │ All 50+     │ ──────► │ Publish     │
    └─────────────┘          └─────────────┘         └─────────────┘
```

---

## Technical Stack (Current MVP + Planned Extensions)

| Component | Technology |
|-----------|------------|
| Frontend | React, TypeScript |
| LMS Integration | LTI 1.3 |
| Backend | Python (FastAPI) |
| LLM | Ollama (current local MVP), OpenAI/Claude planned |
| Code Execution | Docker (planned sandbox) |
| Database | PostgreSQL (implemented primary database), MongoDB planned |
| Cache | Redis (planned) |
| Cloud | AWS / GCP / Azure (planned) |

---

## Competitive Analysis

### Existing Solutions

| Product | Limitations |
|---------|-------------|
| ELICE | Not integrated with iCollege |
| Gradescope | Limited AI feedback |
| CodeGrade | No historical context preservation |

### Agentic TA Advantages

- Direct iCollege integration (no context switching)
- Preserves grading context from previous semesters
- OCR for handwritten components
- Proactive flagging of at-risk students
- Mandatory approval workflow (human-in-the-loop)

---

## Project Structure

```
agentic_ta/
├── README.md                          # This file
├── docs/
│   ├── SRS.md                         # Software Requirements Specification
│   └── integration_architecture.md    # Integration & Architecture Documentation
├── mockups/
│   ├── icollege_integration.html      # Main integration mockup
│   ├── rubric_configuration.html      # Rubric setup mockup
│   ├── batch_grading.html             # Batch grading mockup
│   ├── approval_workflow.html         # Approval workflow mockup
│   └── analytics_dashboard.html       # Analytics dashboard mockup
└── figures/
    ├── page1.png                      # iCollege assignments page
    └── page2.png                      # iCollege submissions page
```

---

## Team

Georgia State University - Software Engineering Course Project (Spring 2026)

---

## License

This project is for educational purposes as part of GSU coursework.
