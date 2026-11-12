"""Regras do MVP, independentes da interface HTML.

RF-002/US-002,010: criação e validação;
RF-003/US-003,005: visibilidade;
RF-004/US-004: atribuição e reatribuição;
RF-005/US-006: tratamento; RF-006/US-007: resolução;
RF-007/US-008: regresso; RF-008/US-009: fecho;
RF-009/US-009: supervisão.
"""
from fastapi import HTTPException
from .auth import require
CATEGORIES = ("Hardware", "Software", "Access")

def error(message, status=400):
    raise HTTPException(status_code=status, detail=message)

def get(db, ticket_id):
    row = db.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    if row is None:
        error("O ticket solicitado não existe.", 404)
    return dict(row)

def allowed(user, ticket):
    """A manager vê todos; os restantes apenas os tickets autorizados."""
    return (user["role"] == "responsavel"
            or (user["role"] == "employee" and ticket["creator_id"] == user["id"])
            or (user["role"] == "technician" and ticket["technician_id"] == user["id"]))

def view(db, user, ticket_id):
    ticket = get(db, ticket_id)
    if not allowed(user, ticket):
        error("Não tem autorização para consultar este ticket.", 403)
    return ticket

def listing(db, user):
    if user["role"] == "responsavel":
        rows = db.execute("SELECT * FROM tickets ORDER BY id DESC")
    elif user["role"] == "technician":
        rows = db.execute("SELECT * FROM tickets WHERE technician_id=? ORDER BY id DESC", (user["id"],))
    else:
        rows = db.execute("SELECT * FROM tickets WHERE creator_id=? ORDER BY id DESC", (user["id"],))
    return [dict(row) for row in rows]

def create(db, user, title, description, category):
    require(user, "employee")
    if not title.strip():
        error("O título é obrigatório.")
    if not description.strip():
        error("A descrição é obrigatória.")
    if category not in CATEGORIES:
        error("Selecione uma categoria válida: Hardware, Software ou Access.")
    cursor = db.execute(
        "INSERT INTO tickets(title,description,category,creator_id) VALUES(?,?,?,?)",
        (title.strip(), description.strip(), category, user["id"]))
    db.commit()
    return get(db, cursor.lastrowid)

def guarded_update(db, statement, params):
    """Apply validation predicates again atomically at the write boundary.

    PostgreSQL rechecks UPDATE predicates after a concurrent writer commits.
    RETURNING captures this operation's result before another transaction changes it.
    """
    row = db.execute(statement + " RETURNING *", params).fetchone()
    if row is None:
        db.rollback()
        error("The ticket changed concurrently. Reload it and try again.", 409)
    ticket = dict(row)
    db.commit()
    return ticket


def assign(db, user, ticket_id, technician_id):
    require(user, "responsavel")
    ticket = get(db, ticket_id)
    if ticket["state"] not in ("Open", "In Progress"):
        error("A atribuição só é permitida em Open ou In Progress.")
    row = db.execute("SELECT role FROM users WHERE id=?", (technician_id,)).fetchone()
    if not row or row["role"] != "technician":
        error("Selecione um technician válido.")
    return guarded_update(db,
        "UPDATE tickets SET technician_id=? WHERE id=? AND state=? "
        "AND (technician_id=? OR (technician_id IS NULL AND CAST(? AS INTEGER) IS NULL))",
        (technician_id, ticket_id, ticket["state"], ticket["technician_id"], ticket["technician_id"]))

def assigned(db, user, ticket_id, state):
    require(user, "technician")
    ticket = get(db, ticket_id)
    if ticket["technician_id"] != user["id"]:
        error("Este ticket está atribuído a outro technician.", 403)
    if ticket["state"] != state:
        error(f"Operação indisponível: o ticket não está no estado {state}.")
    return ticket

def start(db, user, ticket_id):
    assigned(db, user, ticket_id, "Open")
    return guarded_update(db,
        "UPDATE tickets SET state='In Progress' WHERE id=? AND state='Open' AND technician_id=?",
        (ticket_id, user["id"]))

def resolve(db, user, ticket_id, solution):
    assigned(db, user, ticket_id, "In Progress")
    if not solution.strip():
        error("Registe a solução antes de resolver o ticket.")
    return guarded_update(db,
        "UPDATE tickets SET state='Resolved',resolution=? WHERE id=? "
        "AND state='In Progress' AND technician_id=?",
        (solution.strip(), ticket_id, user["id"]))

def reopen(db, user, ticket_id):
    require(user, "employee")
    ticket = get(db, ticket_id)
    if ticket["creator_id"] != user["id"]:
        error("Não pode alterar tickets de outros employeees.", 403)
    if ticket["state"] != "Resolved":
        error("Apenas tickets Resolveds podem regressar a In Progress.")
    return guarded_update(db,
        "UPDATE tickets SET state='In Progress' WHERE id=? AND state='Resolved' AND creator_id=?",
        (ticket_id, user["id"]))

def close(db, user, ticket_id, confirmed):
    require(user, "responsavel")
    ticket = get(db, ticket_id)
    if ticket["state"] != "Resolved":
        error("Apenas tickets Resolveds podem ser fechados.")
    if not confirmed:
        error("Confirme que verificou a resolução antes de fechar.")
    return guarded_update(db,
        "UPDATE tickets SET state='Closed' WHERE id=? AND state='Resolved'", (ticket_id,))
