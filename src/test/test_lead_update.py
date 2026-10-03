import copy
import unittest

from lead_update import update_lead


def fresh_leads():
    def lead(i, tenant, assigned):
        return {
            "id": i,
            "tenant_id": tenant,
            "assigned_to": assigned,
            "status": "contact_lawyer",
            "version": 1,
        }

    return {
        101: lead(101, "T-A", "U-A"),
        102: lead(102, "T-A", "U-B"),
        201: lead(201, "T-B", "U-X"),
    }

# dados fake para testar
AGENT_A = {"user_id": "U-A", "tenant_id": "T-A", "role": "agent"}
MANAGER_A = {"user_id": "U-M", "tenant_id": "T-A", "role": "manager"}


def body(i=101, status="sent_to_funder", version=1, **extra):
    return {"id": i, "status": status, "version": version, **extra}


class UpdateLeadTests(unittest.TestCase):
    def setUp(self):
        self.leads = fresh_leads()
        self.before = copy.deepcopy(self.leads)

    def assertUnchanged(self):
        self.assertEqual(self.leads, self.before)

    def test_1_unauthenticated_rejected(self):
        code, data = update_lead(None, body(), self.leads)
        self.assertEqual(code, 401)
        self.assertUnchanged()

    def test_2_agent_updates_assigned_lead(self):
        code, data = update_lead(AGENT_A, body(101), self.leads)
        self.assertEqual(code, 200)
        self.assertEqual(data, {"id": 101, "status": "sent_to_funder", "version": 2})
        self.assertEqual(self.leads[101]["status"], "sent_to_funder")
        self.assertEqual(self.leads[101]["version"], 2)
        self.assertEqual(self.leads[102], self.before[102])
        self.assertEqual(self.leads[201], self.before[201])

    def test_3_agent_cannot_update_other_agents_lead(self):
        code, data = update_lead(AGENT_A, body(102), self.leads)
        self.assertEqual(code, 404)
        self.assertEqual(data, {"error": "not_found"})
        self.assertUnchanged()

    def test_4_manager_cannot_update_cross_tenant_lead(self):
        code, data = update_lead(MANAGER_A, body(201), self.leads)
        self.assertEqual(code, 404)
        self.assertEqual(data, {"error": "not_found"})
        self.assertUnchanged()

    def test_5_manager_updates_any_lead_in_tenant(self):
        code, data = update_lead(MANAGER_A, body(102, "cannot_fund"), self.leads)
        self.assertEqual(code, 200)
        self.assertEqual(data, {"id": 102, "status": "cannot_fund", "version": 2})
        self.assertEqual(self.leads[101], self.before[101])
        self.assertEqual(self.leads[201], self.before[201])

    def test_6_unknown_target_status_rejected(self):
        for bad in ("contact_lawyer", "closed", "", None, 5, ["sent_to_funder"], {"a": 1}):
            with self.subTest(status=bad):
                code, _ = update_lead(AGENT_A, body(101, bad), self.leads)
                self.assertEqual(code, 422)
                self.assertUnchanged()

    def test_7_replay_of_original_version_does_not_write_twice(self):
        first, _ = update_lead(AGENT_A, body(101, "sent_to_funder", 1), self.leads)
        self.assertEqual(first, 200)
        after_first = copy.deepcopy(self.leads)
        second, data = update_lead(AGENT_A, body(101, "cannot_fund", 1), self.leads)
        self.assertEqual(second, 409)
        self.assertEqual(self.leads, after_first)
        self.assertEqual(self.leads[101]["status"], "sent_to_funder")
        self.assertEqual(self.leads[101]["version"], 2)

    def test_8a_unknown_role_rejected(self):
        for role in ("admin", "", None, "AGENT", 1):
            with self.subTest(role=role):
                auth = {"user_id": "U-A", "tenant_id": "T-A", "role": role}
                code, _ = update_lead(auth, body(101), self.leads)
                self.assertEqual(code, 403)
                self.assertUnchanged()

    def test_8b_body_fields_cannot_elevate_agent(self):
        evil = body(102, role="manager", tenant_id="T-A", assigned_to="U-A", user_id="U-B")
        code, data = update_lead(AGENT_A, evil, self.leads)
        self.assertEqual(code, 404)
        self.assertUnchanged()
        evil2 = body(201, role="manager", tenant_id="T-B")
        code, _ = update_lead(AGENT_A, evil2, self.leads)
        self.assertEqual(code, 404)
        self.assertUnchanged()

   

if __name__ == "__main__":
    unittest.main(verbosity=2)