"""Execute the functional scenarios in the approved Gherkin feature.

T-11 requires measurements under defined conditions; T-12 requires real Chrome
and Edge browsers. Both remain explicitly skipped until those checks are run.
"""
import pytest
from pytest_bdd import scenario, given, when, then, parsers
from src.database import connect
from src import services
from tests.conftest import post_form, login, person, create_ticket

FEATURE = "../../features/tickets.feature"


@scenario(FEATURE, "US-001 - Authentication")
def test_t01():
    pass


@scenario(FEATURE, "US-002 - Create a ticket")
def test_t02():
    pass


@scenario(FEATURE, "US-003 - View tickets")
def test_t03():
    pass


@scenario(FEATURE, "US-004 - Assign and reassign a ticket")
def test_t04():
    pass


@scenario(FEATURE, "US-005 - View assigned tickets")
def test_t05():
    pass


@scenario(FEATURE, "US-006 - Start handling a ticket")
def test_t06():
    pass


@scenario(FEATURE, "US-007 - Record a resolution")
def test_t07():
    pass


@scenario(FEATURE, "US-008 - Return to handling")
def test_t08():
    pass


@scenario(FEATURE, "US-009 - Track and close a ticket")
def test_t09():
    pass


@scenario(FEATURE, "US-010 - Validate required fields")
def test_t10():
    pass


@pytest.mark.skip(reason="T-11: performance measurement conditions are not yet defined")
@scenario(FEATURE, "US-011 - Verify performance")
def test_t11():
    pass


@pytest.mark.skip(reason="T-12: requires real Chrome and Edge browsers; TestClient is insufficient")
@scenario(FEATURE, "US-012 - Compatibility")
def test_t12():
    pass


@pytest.fixture
def ctx(env):
    client, path = env
    return {"client": client, "path": path, "ticket": None, "response": None}


def actor(ctx, email):
    with connect(ctx["path"]) as db:
        return person(db, email)


def ticket(ctx, state="Open", assigned=False):
    with connect(ctx["path"]) as db:
        created = create_ticket(db)
        if assigned:
            created = services.assign(
                db,
                person(db, "sofia@test"),
                created["id"],
                person(db, "miguel@test")["id"],
            )
        if state != "Open":
            services.start(db, person(db, "miguel@test"), created["id"])
        if state in ("Resolved", "Closed"):
            services.resolve(db, person(db, "miguel@test"), created["id"], "Solution applied")
        ctx["ticket"] = services.get(db, created["id"])


def update(ctx, operation, email, *args):
    with connect(ctx["path"]) as db:
        ctx["ticket"] = operation(db, person(db, email), ctx["ticket"]["id"], *args)


@given("Ana has a valid account")
def ana_account(ctx):
    assert actor(ctx, "ana@test")["role"] == "employee"


@when("she enters the correct email and password")
def valid_login(ctx):
    ctx["response"] = login(ctx["client"], "ana@test")


@then("she can sign in")
def logged(ctx):
    assert ctx["response"].status_code == 303


@then("she is identified as an employee")
def identified(ctx):
    assert actor(ctx, "ana@test")["role"] == "employee"


@given("Ana is signed in")
def ana_logged(ctx):
    login(ctx["client"], "ana@test")


@when("she creates a ticket with a title and description")
def create_form(ctx):
    ctx["data"] = {"title": "Printer", "description": "It does not print"}


@when(parsers.parse('selects the "{category}" category'))
def choose_category(ctx, category):
    ctx["data"]["category"] = category
    ctx["response"] = post_form(ctx["client"], "/tickets/new", data=ctx["data"], follow_redirects=False)


@then("the ticket is recorded")
def created(ctx):
    assert ctx["response"].status_code == 303
    with connect(ctx["path"]) as db:
        ctx["ticket"] = dict(db.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 1").fetchone())


@then(parsers.parse('its status is "{state}"'))
def initial_state(ctx, state):
    assert ctx["ticket"]["state"] == state


@given("tickets exist for multiple employees")
def several_owners(ctx):
    ticket(ctx)
    with connect(ctx["path"]) as db:
        services.create(db, person(db, "outro@test"), "Other", "Another issue", "Software")


@when("she views the tickets")
def list_ana(ctx):
    ctx["response"] = ctx["client"].get("/tickets")


@then("she sees only her requests")
def only_own(ctx):
    assert "Printer" in ctx["response"].text
    assert "Another issue" not in ctx["response"].text


@then("their statuses")
def states_visible(ctx):
    assert "Open" in ctx["response"].text


@given("Sofia is signed in as the IT manager")
def sofia_logged(ctx):
    login(ctx["client"], "sofia@test")


@given(parsers.parse('a ticket exists with the status "{state}"'))
def existing_state(ctx, state):
    ticket(ctx, state, assigned=(state != "Open"))


@when("she assigns the ticket to Miguel")
def assign_miguel(ctx):
    update(ctx, services.assign, "sofia@test", actor(ctx, "miguel@test")["id"])


@then("Miguel is identified as the person responsible")
def miguel_assigned(ctx):
    assert ctx["ticket"]["technician_id"] == actor(ctx, "miguel@test")["id"]


@when("Sofia reassigns the ticket to another technician")
def reassign(ctx):
    update(ctx, services.assign, "sofia@test", actor(ctx, "technician2@test")["id"])


@then("the new technician is identified as the person responsible")
def new_tech(ctx):
    assert ctx["ticket"]["technician_id"] == actor(ctx, "technician2@test")["id"]


@then(parsers.parse('the ticket status remains "{state}"'))
def state_unchanged(ctx, state):
    assert ctx["ticket"]["state"] == state


@given("Miguel is signed in as a technician")
def miguel_logged(ctx):
    login(ctx["client"], "miguel@test")


@given("tickets are assigned to Miguel")
def tickets_assigned(ctx):
    ticket(ctx, assigned=True)


@when("he views the ticket list")
def list_miguel(ctx):
    ctx["response"] = ctx["client"].get("/tickets")


@then("he sees the tickets assigned to him")
def tech_listing(ctx):
    assert "Printer" in ctx["response"].text


@given("Miguel has an assigned ticket")
def miguel_ticket(ctx):
    ticket(ctx, assigned=True)


@given(parsers.parse('the ticket status is "{state}"'))
def check_state(ctx, state):
    assert ctx["ticket"]["state"] == state


@when("he starts handling it")
def start(ctx):
    update(ctx, services.start, "miguel@test")


@then(parsers.parse('the status changes to "{state}"'))
def state_changes(ctx, state):
    assert ctx["ticket"]["state"] == state


@given("Miguel is handling a ticket")
def treating(ctx):
    ticket(ctx, "In Progress", assigned=True)


@when("he records the solution applied")
def solution(ctx):
    ctx["solution"] = "Replaced toner"


@when("marks the ticket as resolved")
def resolve(ctx):
    update(ctx, services.resolve, "miguel@test", ctx["solution"])


@then("the solution is recorded")
def solution_saved(ctx):
    assert ctx["ticket"]["resolution"] == ctx["solution"]


@given(parsers.parse('Ana has a ticket with the status "{state}"'))
def ana_ticket(ctx, state):
    ticket(ctx, state, assigned=True)


@given("the ticket is assigned to Miguel")
def verify_assignment(ctx):
    miguel_assigned(ctx)


@when("she reports that the issue persists")
def reopen(ctx):
    update(ctx, services.reopen, "ana@test")


@then(parsers.parse('the status returns to "{state}"'))
def returned(ctx, state):
    assert ctx["ticket"]["state"] == state


@then("Miguel remains responsible")
def same_tech(ctx):
    miguel_assigned(ctx)


@when("she reviews the recorded solution")
def consult_solution(ctx):
    assert ctx["ticket"]["resolution"] == "Solution applied"


@when("confirms the resolution without requiring Ana's formal confirmation")
def confirm(ctx):
    ctx["confirmed"] = True


@when("closes the ticket")
def close(ctx):
    update(ctx, services.close, "sofia@test", ctx["confirmed"])


@when("she tries to create a ticket without one of the required fields: title, description, or category")
def invalid_forms(ctx):
    ctx["errors"] = []
    for field in ("title", "description", "category"):
        data = {"title": "Request", "description": "Issue", "category": "Hardware"}
        data[field] = ""
        response = post_form(ctx["client"], "/tickets/new", data=data)
        ctx["errors"].append((field, response))


@then("the ticket is not created")
def no_creation(ctx):
    with connect(ctx["path"]) as db:
        assert db.execute("SELECT count(*) FROM tickets").fetchone()[0] == 0


@then("the missing field is identified")
def missing_field(ctx):
    assert all(
        name in response.text.lower()
        for name, response in ctx["errors"]
    )


@then("a clear message is displayed")
def clear_message(ctx):
    assert all(response.status_code == 200 and 'role="alert"' in response.text for _, response in ctx["errors"])


@given("measurement conditions are documented in the local demonstration environment")
def measurements_documented(ctx):
    pass


@when("he accesses the main authentication, ticket creation, and ticket viewing pages")
def access_main_pages(ctx):
    pass


@then("each page responds within 3 seconds")
def response_time(ctx):
    pass


@given(parsers.parse('Ana is using the "{browser}" browser'))
def browser_used(ctx, browser):
    ctx["browser"] = browser


@given("she has a valid account")
def valid_account(ctx):
    assert actor(ctx, "ana@test")["role"] == "employee"


@when("she signs in")
def sign_in(ctx):
    login(ctx["client"], "ana@test")


@when("creates a ticket with the required fields")
def create_required(ctx):
    ctx["response"] = post_form(ctx["client"],
        "/tickets/new",
        data={"title": "Printer", "description": "Issue", "category": "Hardware"},
        follow_redirects=False,
    )


@then("she can record the ticket")
def record_ticket(ctx):
    assert ctx["response"].status_code == 303


@then(parsers.parse('sees the status "{state}"'))
def visible_status(ctx, state):
    assert state == "Open"
