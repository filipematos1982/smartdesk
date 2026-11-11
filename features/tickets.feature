# language: en

Feature: SmartDesk MVP
  As a NexaServ user
  I want to manage IT support requests
  So that I can track their resolution

  Scenario: US-001 - Authentication
    Given Ana has a valid account
    When she enters the correct email and password
    Then she can sign in
    And she is identified as an employee

  Scenario: US-002 - Create a ticket
    Given Ana is signed in
    When she creates a ticket with a title and description
    And selects the "Hardware" category
    Then the ticket is recorded
    And its status is "Open"

  Scenario: US-003 - View tickets
    Given Ana is signed in
    And tickets exist for multiple employees
    When she views the tickets
    Then she sees only her requests
    And their statuses

  Scenario: US-004 - Assign and reassign a ticket
    Given Sofia is signed in as the IT manager
    And a ticket exists with the status "Open"
    When she assigns the ticket to Miguel
    Then Miguel is identified as the person responsible
    When Sofia reassigns the ticket to another technician
    Then the new technician is identified as the person responsible
    And the ticket status remains "Open"

  Scenario: US-005 - View assigned tickets
    Given Miguel is signed in as a technician
    And tickets are assigned to Miguel
    When he views the ticket list
    Then he sees the tickets assigned to him

  Scenario: US-006 - Start handling a ticket
    Given Miguel has an assigned ticket
    And the ticket status is "Open"
    When he starts handling it
    Then the status changes to "In Progress"

  Scenario: US-007 - Record a resolution
    Given Miguel is handling a ticket
    And the ticket status is "In Progress"
    When he records the solution applied
    And marks the ticket as resolved
    Then the status changes to "Resolved"
    And the solution is recorded

  Scenario: US-008 - Return to handling
    Given Ana has a ticket with the status "Resolved"
    And the ticket is assigned to Miguel
    When she reports that the issue persists
    Then the status returns to "In Progress"
    And Miguel remains responsible

  Scenario: US-009 - Track and close a ticket
    Given Sofia is signed in as the IT manager
    And a ticket exists with the status "Resolved"
    When she reviews the recorded solution
    And confirms the resolution without requiring Ana's formal confirmation
    And closes the ticket
    Then the status changes to "Closed"

  Scenario: US-010 - Validate required fields
    Given Ana is signed in
    When she tries to create a ticket without one of the required fields: title, description, or category
    Then the ticket is not created
    And the missing field is identified
    And a clear message is displayed

  Scenario: US-011 - Verify performance
    Given Miguel is signed in
    And measurement conditions are documented in the local demonstration environment
    When he accesses the main authentication, ticket creation, and ticket viewing pages
    Then each page responds within 3 seconds

  Scenario Outline: US-012 - Compatibility
    Given Ana is using the "<browser>" browser
    And she has a valid account
    When she signs in
    And creates a ticket with the required fields
    Then she can record the ticket
    And sees the status "Open"

    Examples:
      | browser |
      | Chrome  |
      | Edge    |
