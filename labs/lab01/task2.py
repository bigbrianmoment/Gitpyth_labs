import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from shared.student import STUDENT_NAME, GROUP_NAME, VARIANT_NUMBER


users = {
    "security_chief": {"role": "security_officer", "clearance": 4, "department": "Security", "active": True},
    "network_admin": {"role": "network_admin", "clearance": 3, "department": "Network", "active": True},
    "help_desk": {"role": "support", "clearance": 1, "department": "Support", "active": True},
    "auditor_ext": {"role": "auditor", "clearance": 3, "department": "Audit", "active": True},
    "temp_worker": {"role": "temporary", "clearance": 1, "department": "Temp", "active": False}
}

resources = [("incident_reports", 4), ("network_topology", 3), ("user_manual", 1),
             ("vulnerability_scans", 3), ("root_access", 4), ("help_tickets", 1),
             ("penetration_tests", 4), ("firewall_rules", 3), ("software_licenses", 2),
             ("faq_docs", 1)]

security_levels = ("Unrestricted", "Limited", "Sensitive", "Classified")

blocked_users = {"temp_worker", "fired_employee", "compromised_acc"}


def level_name(level):
    return security_levels[level - 1]


def check_access(username, resource_level):
    if username not in users:
        return "DENY", "User not found"

    if username in blocked_users:
        return "DENY", "User is blocked"

    user = users[username]

    if not user["active"]:
        return "DENY", "Account inactive"

    if user["clearance"] >= resource_level:
        return "ALLOW", None

    return "DENY", "Insufficient clearance"


def main():
    print(f"Виконав: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}\n")


    print("Ресурси системи:")
    for name, level in resources:
        print(f"  {name:<20} -> {level_name(level)}")
    print()


    print("Результати перевірки доступу:\n")


    all_usernames = list(users.keys()) + list(blocked_users - users.keys())

    for username in all_usernames:
        for resource_name, resource_level in resources:
            decision, reason = check_access(username, resource_level)
            if decision == "ALLOW":
                print(f"user={username} resource={resource_name} -> ALLOW")
            else:
                print(f"user={username} resource={resource_name} -> DENY ({reason})")


if __name__ == "__main__":
    main()