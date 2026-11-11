# Step 1 — SmartDesk Business Problem and Objectives

## 1. Business Problem

NexaServ is a consulting and technology services company with 60 employees, distributed between its headquarters and remote work.

Currently, IT support requests are submitted by email, phone, or messaging. The IT team, consisting of three technicians and one manager, uses a shared mailbox and a spreadsheet to manage requests.

This process has three main problems:

- Some requests are lost or are not properly recorded.
- It is not always clear who is responsible for each request.
- It is difficult to track the status and resolution of issues.

## 2. Project Objectives

SmartDesk aims to centralize and organize IT support requests in a single internal web application.

The main objectives are:

1. Ensure that all requests are recorded.
2. Enable tickets to be assigned to technicians.
3. Track each request from submission through closure.
4. Facilitate communication between employees and the IT team.
5. Improve the organization and oversight of support work.

## 3. Expected Improvements

| Current situation | Intended improvement |
|---|---|
| Requests are spread across multiple channels | Requests are centralized in SmartDesk |
| Risk of losing requests | Tickets are recorded in an organized manner |
| Unclear responsibilities | The responsible technician is identified |
| Difficulty tracking requests | Statuses are visible and up to date |
| Oversight through a spreadsheet | Centralized oversight by the IT manager |

## 4. First-Version Scope (MVP)

The first version will include ticket management for the Hardware, Software, and Access categories.

The workflow will be: **Open → In Progress → Resolved → Closed**, supporting ticket creation, assignment, handling, resolution, and closure.

There will be three roles: employee, support technician, and IT manager.

The MVP excludes a mobile application, SMS notifications, automated AI-based resolution, email integration, and complex SLA (service-level deadline) management.

## 5. Confirmed Decisions

- **Ticket visibility:** employees see only their own tickets; technicians see tickets assigned to them; Sofia sees all tickets (RF-003).
- **Closure:** only Sofia may close Resolved tickets after verifying the resolution; Ana's formal confirmation is not required (RF-008).
- **Required fields:** title, description, and category (RF-002).
- **Priorities:** P0/P1 organize development; tickets are not assigned a priority in the MVP.

**Pending operational definition:** measurement conditions for the provisional three-second target (RNF-002). See [requirements](../produto/02_requisitos_e_user_stories.md) and [MVP](../produto/03_mvp_backlog_e_aceitacao.md).
