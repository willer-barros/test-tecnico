# Section C

# roles de teste
ALLOWED_ROLES = {"agent", "manager"}
TARGET_STATUSES = {"sent_to_funder", "cannot_fund"}
REQUIRED_STATE = "contact_lawyer"


def _positive_int(value):
    return type(value) is int and value > 0


def update_lead(auth, body, leads):
    if (
        not isinstance(auth, dict)
        or not auth.get("user_id")
        or not auth.get("tenant_id")
    ):
        return 401, {"error": "unauthenticated"}

    role = auth.get("role")
    if not isinstance(role, str) or role not in ALLOWED_ROLES:
        print(type(role))
        return 403, {"error": "forbidden"}

    if not isinstance(body, dict):
        return 422, {"error": "invalid_body"}
    lead_id = body.get("id")
    version = body.get("version")
    status = body.get("status")
    if not _positive_int(lead_id) or not _positive_int(version):
        return 422, {"error": "invalid_body"}
    if not isinstance(status, str) or status not in TARGET_STATUSES:
        return 422, {"error": "invalid_status"}

    lead = leads.get(lead_id)
    if lead is None or lead["tenant_id"] != auth["tenant_id"]:
        return 404, {"error": "not_found"}
    if role == "agent" and lead["assigned_to"] != auth["user_id"]:
        return 404, {"error": "not_found"}

    if lead["version"] != version:
        return 409, {"error": "version_conflict"}

    if lead["status"] != REQUIRED_STATE:
        return 422, {"error": "invalid_transition"}

    lead["status"] = status
    lead["version"] += 1
    return 200, {"id": lead["id"], "status": lead["status"], "version": lead["version"]}