# Step 4 — Requirements, User Stories, and Acceptance Criteria

**Status:** Version 2 approved.

## 1. Functional Requirements (RF)

| ID | Requirement | Description |
|---|---|---|
| RF-001 | Authentication | Access using email and password, with role identification. |
| RF-002 | Ticket creation | Record the required title, description, and category fields: Hardware, Software, or Access. |
| RF-003 | Ticket visibility | Employees can view their own tickets; technicians can view assigned tickets; the manager can view all tickets. |
| RF-004 | Assignment and reassignment | Sofia can assign or reassign tickets, including tickets that are In Progress. |
| RF-005 | Start handling | The responsible technician changes the status from Open to In Progress. |
| RF-006 | Resolution | The technician records the solution and changes the status to Resolved. |
| RF-007 | Return to handling | An employee reports that the issue persists; the ticket moves from Resolved to In Progress. |
| RF-008 | Closure | Only Sofia may close Resolved tickets after verifying and confirming the resolution; the employee's formal confirmation is not required. Closed tickets cannot be reopened. |
| RF-009 | Oversight | Sofia can view tickets, categories, statuses, and responsible technicians. |

## 2. Non-Functional Requirements (RNF)

| ID | Requirement | Verification criterion |
|---|---|---|
| RNF-001 | Usability | An employee can create a ticket without technical knowledge, using clear fields and messages. |
| RNF-002 | Performance | The main pages respond within 3 seconds under normal usage conditions. This is an approved provisional target; the pages and measurement conditions will be documented before testing. |
| RNF-003 | Security | Access is authenticated, and operations are limited according to each role's permissions. |
| RNF-004 | Compatibility | The application works in Chrome and Edge on a computer. |

## 3. User Stories (US)

| ID | Persona | User Story | Requirements |
|---|---|---|---|
| US-001 | Ana | As Ana, I want to sign in with my email and password so that I can access my requests securely. | RF-001, RNF-003 |
| US-002 | Ana | As Ana, I want to create a ticket so that I can report an IT issue. | RF-002, RNF-001 |
| US-003 | Ana | As Ana, I want to view my tickets so that I can track their resolution. | RF-003 |
| US-004 | Sofia | As Sofia, I want to assign and reassign tickets so that I can distribute the work among technicians. | RF-004, RNF-003 |
| US-005 | Miguel | As Miguel, I want to view the tickets assigned to me so that I can organize my work. | RF-003 |
| US-006 | Miguel | As Miguel, I want to start handling a ticket so that I can indicate that I am resolving the issue. | RF-005 |
| US-007 | Miguel | As Miguel, I want to record the solution and mark the ticket as Resolved so that I can document the intervention. | RF-006 |
| US-008 | Ana | As Ana, I want to report that the issue persists so that the ticket returns to In Progress. | RF-007 |
| US-009 | Sofia | As Sofia, I want to track tickets and close resolved ones so that I can oversee support. | RF-008, RF-009 |
| US-010 | Ana | As Ana, I want a simple form that identifies required fields and displays clear error messages so that I can create tickets correctly. | RF-002, RNF-001 |
| US-011 | Miguel | As Miguel, I want to view assigned tickets quickly so that I can organize my work without unnecessary delays. | RF-003, RNF-002 |
| US-012 | Ana | As Ana, I want to use SmartDesk in Chrome and Edge so that I can access the application and create tickets in the available browser. | RF-001, RF-002, RNF-004 |

US-010, US-011, and US-012 reinforce usability, performance, and compatibility, respectively. Authentication was included to distinguish the three roles. Reassignment and returning a ticket to handling follow the approved journey. No functionality outside the MVP is introduced.

## 4. Gherkin Acceptance Criteria

The approved acceptance scenarios are in [features/tickets.feature](../../features/tickets.feature). Each scenario identifies its corresponding User Story.

## 5. Traceability Matrix

| Requirement | Related User Stories | Verification |
|---|---|---|
| RF-001 | US-001, US-012 | Authentication and access |
| RF-002 | US-002, US-010, US-012 | Creation and validation |
| RF-003 | US-003, US-005, US-011 | Ticket visibility |
| RF-004 | US-004 | Assignment and reassignment |
| RF-005 | US-006 | Start handling |
| RF-006 | US-007 | Recording the resolution |
| RF-007 | US-008 | Return to handling |
| RF-008 | US-009 | Closure and restrictions |
| RF-009 | US-009 | Oversight |
| RNF-001 | US-002, US-010 | Form and messages |
| RNF-002 | US-011 | Response time |
| RNF-003 | US-001, US-004, US-009 | Authentication and permissions |
| RNF-004 | US-012 | Chrome and Edge |

**Traceability coverage:** 13/13 requirements are associated with at least one User Story; 12/12 User Stories are associated with requirements and have at least one Gherkin scenario. Traceability alone does not demonstrate complete test coverage.

US-011 requires response-time measurements under previously defined usage conditions. US-012 requires execution in both browsers. The remaining scenarios include functional and permission checks.

## 6. Confirmed Decisions

1. Authentication uses **email and password**.
2. Ana can report that an issue persists and return a **Resolved** ticket to **In Progress**.
3. Only Sofia may close **Resolved** tickets after verifying the resolution; Ana's formal confirmation is not required.
4. The provisional response-time target for the main pages is **within 3 seconds**, with measurement conditions to be documented before testing.
5. **Title, description, and category** are required when creating tickets.

**Scope preserved:** employee, support technician, and IT manager roles; Hardware, Software, and Access categories; Open, In Progress, Resolved, and Closed statuses. Outside the MVP: mobile application, SMS, automated AI-based resolution, email integration, and complex SLA management.
