# Step 5 — MVP, Backlog, and Acceptance Criteria

**Status:** Approved proposal.

## 1. Proposed MVP

The SmartDesk MVP demonstrates a complete IT support journey:

1. **Ana** signs in and creates a printer ticket in the **Hardware** category — status **Open**.
2. **Sofia** reviews the request and assigns it to **Miguel** — status **Open**.
3. **Miguel** views the ticket and starts handling it — status **In Progress**.
4. **Miguel** records the solution — status **Resolved**.
5. **Sofia** verifies and confirms the resolution, then closes the ticket without requiring Ana's formal confirmation — status **Closed**.

**Alternative path:** If Ana reports that the issue persists, a **Resolved** ticket returns to **In Progress**, retaining the responsible technician unless Sofia reassigns it.

This is a small, demonstrable workflow that covers the essential SmartDesk ticket lifecycle.

## 2. Prioritized Backlog

- **P0 — Essential:** required to demonstrate the complete workflow.
- **P1 — Complementary:** required to meet the approved MVP, although not essential to the first demonstration.
- **P2 — Later:** improvements for after the first demonstrable version.

| Priority | US | Functionality | Decision |
|---|---|---|---|
| P0 | US-001 | Email and password authentication with three roles | MVP |
| P0 | US-002 | Create a ticket with a title, description, and category | MVP |
| P0 | US-003 | Ana views her tickets | MVP |
| P0 | US-004 | Sofia assigns tickets to technicians | MVP |
| P0 | US-005 | Miguel views assigned tickets | MVP |
| P0 | US-006 | Miguel starts handling a ticket | MVP |
| P0 | US-007 | Miguel records a resolution | MVP |
| P0 | US-009 | Sofia tracks and closes tickets | MVP |
| P1 | US-008 | Ana reports a persistent issue and returns the ticket to In Progress | MVP |
| P1 | US-010 | Required-field validation and clear messages | MVP |
| P1 | US-011 | Ticket pages respond within 3 seconds | MVP |
| P1 | US-012 | Works in Chrome and Edge | MVP |

**Note:** Ticket reassignment in US-004 is part of the MVP, even though it is not required for the primary workflow. P0 and P1 indicate work order, not MVP exclusions or ticket priorities. The MVP has no ticket-priority field.

## 3. Included in the MVP and Later Evolution

**Included:** authentication; ticket creation and viewing; assignment and reassignment; handling and resolution; return to handling; oversight and closure; validation of required fields (title, description, and category); permissions; Chrome/Edge compatibility; provisional response-time target of up to 3 seconds.

**Outside the MVP:** mobile application, SMS notifications, automatic email integration, automated AI-based resolution, and advanced SLA management. These features will not be specified or implemented in this phase.

**Roles:** employee (Ana Martins), support technician (Miguel Costa), IT manager (Sofia Almeida).

**Categories:** Hardware, Software, and Access.

**Statuses:** Open, In Progress, Resolved, and Closed.

## 4. Gherkin Acceptance Criteria

The file [`features/tickets.feature`](../../features/tickets.feature) contains the **12 main scenarios**, one for each User Story (US-001 through US-012), revised for the MVP. This simplification replaces the previous 16 scenarios while retaining their identifiers.

Reassignment, closure exclusively by Sofia, and the prohibition on reopening closed tickets remain mandatory rules, even though this simplified version has no separate negative scenarios for them.

## 5. Mandatory Business Rules

| Rule | Expected behavior |
|---|---|
| Roles | Employees, technicians, and the IT manager have distinct permissions. |
| Categories | Only Hardware, Software, and Access are allowed. |
| Statuses | Open, In Progress, Resolved, and Closed. |
| Reassignment | Sofia can reassign tickets, including those that are In Progress. |
| Return to handling | Ana can return a Resolved ticket to In Progress. |
| Closure | Only Sofia may close a Resolved ticket after verifying the resolution; Ana's formal confirmation is not required. |
| Closed ticket | Cannot be reopened. |

These rules must continue to be verified during testing.

## 6. MVP Completion Criteria

The MVP will be demonstrable when:

- Ana can sign in, create a ticket, and track its status.
- Sofia can assign and reassign tickets.
- Miguel can view, handle, and resolve assigned tickets.
- Ana can report that a resolution did not work.
- Sofia can oversee and close a resolved ticket.
- Permissions, categories, statuses, and transition rules are respected.
- Usability, performance, and compatibility criteria have been verified.

**Note:** The target of up to 3 seconds is provisional and requires measurement under previously defined conditions. Compatibility must be verified in Chrome and Edge.

## 7. Traceability

The MVP retains the 12 User Stories and requirements RF-001 through RF-009 and RNF-001 through RNF-004 approved in [Step 4](02_requisitos_e_user_stories.md). Each scenario in `features/tickets.feature` identifies its User Story. No new personas or functionality have been added.
