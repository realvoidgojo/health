from app.views.console.ui import print_card, display_header, print_info, print_error, print_success
from app.core.formatting import format_inr
from typing import List, Dict

class Menus:
    @staticmethod
    def print_report_card(data, title: str):
        fields = [(k.replace('_', ' ').title(), v) for k, v in dict(data).items()]
        print_card(title, fields)

    @staticmethod
    def print_available_policies(policies: List[Dict]):
        if not policies:
            print_info("No policies available at the moment.")
            return

        for p in policies:
            print_card(
                f"[{p['policy_id']}] {p['policy_name']}",
                [
                    ("Category", p['category']),
                    ("Sum Insured", format_inr(p['sum_insured'])),
                    ("Premium", f"{format_inr(p['premium_amount'])}/mon (Billed Annually)"),
                    ("Coverage Details", p['coverage_details'])
                ]
            )

    @staticmethod
    def print_my_policies(policies: List[Dict], admin_mode=False):
        if not policies:
            print_info("No policies found.")
            return

        for p in policies:
            title = f"POLICY #{p['customer_policy_id']} - {p['policy_name']}"
            if admin_mode:
                title = f"[{p['customer_policy_id']}] Customer: {p['cust_name']} | Policy: {p['policy_name']}"
                
            fields = [
                ("Status", p['status']),
                ("Nominee Name", p['nominee_name']),
                ("Nominee Relation", p['nominee_relation']),
                ("Start Date", p['start_date'] or 'Pending'),
                ("Expiry Date", p['expiry_date'] or 'Pending'),
                ("Agent Remarks", p['agent_remarks'] or 'None')
            ]
            if admin_mode:
                fields.insert(1, ("Customer ID", p['customer_id']))
                
            print_card(title, fields)

    @staticmethod
    def print_my_claims(claims: List[Dict], admin_mode=False):
        if not claims:
            print_info("No claims found.")
            return

        for c in claims:
            title = f"CLAIM #{c['claim_id']}"
            if admin_mode:
                title += f" (Policy ID: {c['policy_id']})"
                
            fields = [
                ("Policy ID", c['customer_policy_id']) if not admin_mode else ("Customer ID", c['customer_id']),
                ("Claim Amount", format_inr(c['claim_amount'])),
                ("Status", c['status']),
                ("Claim Reason", c['claim_reason']),
                ("Officer Remarks", c['additional_details'] or 'None')
            ]
            if admin_mode:
                fields.append(("Assigned Officer ID", c['claim_officer_id'] or 'Unassigned'))
                
            print_card(title, fields)

    @staticmethod
    def print_reactivation_requests(requests: List[Dict]):
        if not requests:
            print_info("No pending reactivation requests.")
            return

        for r in requests:
            print_card(
                f"REQUEST #{r['request_id']}",
                [
                    ("User ID", r['user_id']),
                    ("User Email", r['email']),
                    ("Request Date", r['request_date'])
                ]
            )

    @staticmethod
    def print_users(users: List[Dict]):
        if not users:
            print_info("No users found.")
            return

        for u in users:
            print_card(
                f"[{u['user_id']}] {u['full_name']}",
                [
                    ("Email", u['email']),
                    ("Phone", u['phone']),
                    ("Role", u['role']),
                    ("Status", "ACTIVE" if u['is_active'] else "INACTIVE")
                ]
            )

    @staticmethod
    def print_claim_history(history: List[Dict]):
        display_header("CLAIM HISTORY LOG")
        if not history:
            print_info("No history logs found for this claim.")
            return
            
        for h in history:
            print(f"[{h['created_at']}] Officer ID {h['officer_id']} - {h['action_taken']}")
            if h['remarks']:
                print(f"  Remarks: {h['remarks']}")
            print("-" * 50)
