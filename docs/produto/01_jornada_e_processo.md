# Step 3 — User Journey and Ticket Process

**Objective:** Describe the journey of an IT support request, from reporting the issue through ticket closure.

## 1. Narrative Sequence — Printer Issue

| Step | Owner | Action | Ticket status |
|---|---|---|---|
| 1 | **Ana Martins** | The printer is not working. Ana accesses SmartDesk and creates a ticket in the Hardware category, describing the issue. | Open |
| 2 | **Sofia Almeida** | Reviews pending requests and assigns the ticket to Miguel, taking the team's workload into account. | Open |
| 3 | **Miguel Costa** | Views the assigned ticket and begins investigating the issue. | In Progress |
| 4 | **Miguel Costa** | Inspects the printer, identifies the cause, and performs the required intervention. | In Progress |
| 5 | **Miguel Costa** | Records the solution applied and marks the ticket as resolved. | Resolved |
| 6 | **Ana Martins** | Can review the resolution and report if the issue persists; formal confirmation is not required for closure. | Resolved |
| 7 | **Sofia Almeida** | Verifies and confirms the resolution, then closes the ticket without requiring Ana's formal confirmation. | Closed |

## 2. Key Process Decisions

- **Who handles the request?** Sofia assigns the ticket to a technician and may reassign it if needed.
- **Was the issue resolved?** If not, Miguel continues handling it.
- **Did the resolution work?** If Ana reports that the issue persists, the ticket moves from Resolved back to In Progress.
- **Can the ticket be closed?** Sofia verifies and confirms the resolution before closing it; Ana's formal confirmation is not required.
- **Can a closed ticket be reopened?** No. A new issue requires a new ticket.

## 3. ASCII Flowchart — Ticket Journey

```text
ANA creates ticket — OPEN
        |
        v
SOFIA assigns to Miguel — OPEN
        |
        v
MIGUEL starts handling — IN PROGRESS
        |
        v
  Issue resolved?
      | NO                   YES
      |                       |
      |                       v
      |             MIGUEL records solution — RESOLVED
      |                       |
      |                       v
      |               Does the resolution hold?
      |                 | NO          YES
      |                 |             |
      |       ANA reports issue       SOFIA verifies and confirms
      |                 |             |
      |                 v             v
      +-------> IN PROGRESS       SOFIA closes — CLOSED
                       |
                       +----> MIGUEL resumes handling
```

If the issue is not resolved, it remains **In Progress**. If Ana reports that it persists after resolution, the ticket returns to **In Progress**, retaining the responsible technician. Sofia may reassign a ticket in **Open** or **In Progress** without changing its status automatically. Only Sofia closes a ticket after verifying the resolution; Ana's formal confirmation is not required. A **Closed** ticket cannot be reopened.

## 4. Expected Outcome

SmartDesk makes it possible to see who reported the issue, who is responsible for handling it, what solution was applied, and the request's current status.
