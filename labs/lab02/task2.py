import argparse
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

logger = logging.getLogger("lab02.firewall_audit")

# Регулярний вираз для IPv4-адреси з опціональною маскою CIDR (/0 - /32)
IP_CIDR_PATTERN = re.compile(
    r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(?:/(\d{1,2}))?$"
)

# Порт: число або спеціальне значення ANY
PORT_PATTERN = re.compile(r"^\d{1,5}$")

VALID_ACTIONS = {"ALLOW", "DENY"}


def setup_logging(log_level: str) -> None:
    """Налаштовує формат виводу логів у стилі [LEVEL] повідомлення."""
    logging.basicConfig(
        level=log_level.upper(),
        format="[%(levelname)s] %(message)s",
        stream=sys.stdout,
    )


def is_valid_ip_or_cidr(value: str) -> bool:
    """Перевіряє, чи є рядок коректною IPv4-адресою (з опціональною маскою)."""
    match = IP_CIDR_PATTERN.match(value)
    if not match:
        return False

    octets = match.groups()[:4]
    mask = match.group(5)

    for octet in octets:
        if not (0 <= int(octet) <= 255):
            return False

    return mask is None or 0 <= int(mask) <= 32


def is_valid_port(value: str) -> bool:
    """Перевіряє порт: або ANY, або число від 1 до 65535."""
    if value == "ANY":
        return True
    if not PORT_PATTERN.match(value):
        return False
    return 1 <= int(value) <= 65535


def load_rules(rules_file: str) -> list[dict]:
    """Зчитує правила фаєрвола з JSON-файлу."""
    path = Path(rules_file)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def validate_rules(rules: list[dict]) -> tuple[list[dict], list[dict]]:
    """Розділяє правила на коректні та некоректні за форматом.

    Повертає (valid_rules, invalid_entries), де invalid_entries
    містить словники з ключами id і reason.
    """
    valid_rules = []
    invalid_entries = []

    for rule in rules:
        rule_id = rule.get("id")
        reasons = []

        if not is_valid_ip_or_cidr(rule.get("source", "")):
            reasons.append(f"invalid source IP: {rule.get('source')}")

        if not is_valid_ip_or_cidr(rule.get("destination", "")):
            reasons.append(f"invalid destination IP: {rule.get('destination')}")

        if not is_valid_port(rule.get("port", "")):
            reasons.append(f"invalid port: {rule.get('port')}")

        if rule.get("action") not in VALID_ACTIONS:
            reasons.append(f"invalid action: {rule.get('action')}")

        if reasons:
            invalid_entries.append({"id": rule_id, "reasons": reasons})
            logger.warning("Rule #%s rejected: %s", rule_id, "; ".join(reasons))
        else:
            valid_rules.append(rule)

    return valid_rules, invalid_entries


def find_duplicates(valid_rules: list[dict]) -> list[dict]:
    """Шукає правила, що повністю повторюються (однакові source,
    destination, port, action). Повертає список груп дублікатів."""
    counter = Counter(
        (r["source"], r["destination"], r["port"], r["action"]) for r in valid_rules
    )

    duplicates = []
    for key, count in counter.items():
        if count > 1:
            source, destination, port, action = key
            matching_ids = [
                r["id"]
                for r in valid_rules
                if (r["source"], r["destination"], r["port"], r["action"]) == key
            ]
            duplicates.append(
                {
                    "ids": matching_ids,
                    "source": source,
                    "destination": destination,
                    "port": port,
                    "action": action,
                    "extra_count": count - 1,
                }
            )

    return duplicates


def find_conflicts(valid_rules: list[dict]) -> list[dict]:
    """Групує правила за (source, destination, port) і шукає групи,
    де одночасно є і ALLOW, і DENY для того самого трафіку."""
    groups = defaultdict(list)
    for rule in valid_rules:
        key = (rule["source"], rule["destination"], rule["port"])
        groups[key].append(rule)

    conflicts = []
    for key, group in groups.items():
        actions = {r["action"] for r in group}
        if len(actions) > 1:
            allow_ids = [r["id"] for r in group if r["action"] == "ALLOW"]
            deny_ids = [r["id"] for r in group if r["action"] == "DENY"]
            conflicts.append(
                {
                    "source": key[0],
                    "destination": key[1],
                    "port": key[2],
                    "allow_ids": allow_ids,
                    "deny_ids": deny_ids,
                }
            )

    return conflicts


def find_high_risk_rules(valid_rules: list[dict]) -> list[dict]:
    """Шукає небезпечні ALLOW-правила: відкритий порт (ANY)
    або джерело 0.0.0.0/0 (весь інтернет)."""
    high_risk = []
    for rule in valid_rules:
        if rule["action"] != "ALLOW":
            continue

        is_open_port = rule["port"] == "ANY"
        is_open_source = rule["source"] == "0.0.0.0/0"

        if is_open_port or is_open_source:
            high_risk.append(rule)

    return high_risk


def save_cleaned_rules(valid_rules: list[dict], output_path: str) -> None:
    """Зберігає список коректних правил у новий JSON-файл."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(valid_rules, f, ensure_ascii=False, indent=2)


def print_report(
    total_rules: int,
    invalid_entries: list[dict],
    duplicates: list[dict],
    conflicts: list[dict],
    high_risk: list[dict],
    checked_conflicts: bool,
) -> None:
    """Виводить підсумковий звіт у консоль."""
    duplicate_count = sum(d["extra_count"] for d in duplicates)

    print("\n=== Firewall Configuration Audit Report ===")
    print(f"Invalid IP/Port/Action Entries : {len(invalid_entries)}")

    if checked_conflicts:
        print(f"Conflicting Rules              : {len(conflicts)} conflicts found")
        print(f"Duplicate Rules                 : {duplicate_count} duplicates found")
    else:
        print("Conflicting Rules               : not checked (use --check-conflicts)")
        print("Duplicate Rules                  : not checked (use --check-conflicts)")

    print(
        f"High-Risk Rules                 : {len(high_risk)} dangerous ALLOW ALL rules"
    )

    print("\n=== Critical Findings ===")

    for entry in invalid_entries:
        print(f"[INVALID] Rule #{entry['id']}: {', '.join(entry['reasons'])}")

    if checked_conflicts:
        for conflict in conflicts:
            allow_str = ", ".join(f"#{i}" for i in conflict["allow_ids"])
            deny_str = ", ".join(f"#{i}" for i in conflict["deny_ids"])
            print(
                f"[CONFLICT] ALLOW rules ({allow_str}) conflict with "
                f"DENY rules ({deny_str}) for {conflict['source']} -> "
                f"{conflict['destination']}:{conflict['port']}"
            )

        for dup in duplicates:
            ids_str = ", ".join(f"#{i}" for i in dup["ids"])
            print(
                f"[DUPLICATE] Rules {ids_str} are identical: "
                f"{dup['action']} {dup['source']} -> {dup['destination']}:{dup['port']}"
            )

    for rule in high_risk:
        reason = "Port: ANY" if rule["port"] == "ANY" else "Source: 0.0.0.0/0"
        print(
            f"[HIGH-RISK] Rule #{rule['id']}: ALLOW {rule['source']} -> "
            f"{rule['destination']}:{rule['port']} ({reason})"
        )


def run_analysis(args: argparse.Namespace) -> None:
    """Головна точка входу для аналізу правил фаєрвола."""
    setup_logging(args.log_level)

    logger.info("Parsing firewall rules from %s...", args.rules_file)

    try:
        rules = load_rules(args.rules_file)
    except FileNotFoundError:
        logger.error("Файл правил не знайдено: %s", args.rules_file)
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error("Некоректний формат JSON у файлі правил: %s", e)
        sys.exit(1)
    except (OSError, PermissionError) as e:
        logger.error("Помилка доступу до файлу правил: %s", e)
        sys.exit(1)

    logger.info(
        "Total rules parsed: %d. Validating IP syntax and rule logic...", len(rules)
    )

    valid_rules, invalid_entries = validate_rules(rules)

    duplicates = []
    conflicts = []
    if args.check_conflicts:
        duplicates = find_duplicates(valid_rules)
        conflicts = find_conflicts(valid_rules)

    high_risk = find_high_risk_rules(valid_rules)

    print_report(
        total_rules=len(rules),
        invalid_entries=invalid_entries,
        duplicates=duplicates,
        conflicts=conflicts,
        high_risk=high_risk,
        checked_conflicts=args.check_conflicts,
    )

    if args.output:
        try:
            save_cleaned_rules(valid_rules, args.output)
            logger.info("Security report successfully exported to %s", args.output)
        except (OSError, PermissionError) as e:
            logger.error("Не вдалося зберегти звіт: %s", e)


def main() -> None:
    """Дозволяє запускати task2.py окремо, без main.py, для тестування."""
    parser = argparse.ArgumentParser(description="Аналізатор правил фаєрвола")
    parser.add_argument("--rules-file", required=True, help="Шлях до файлу правил")
    parser.add_argument("--output", help="Шлях до файлу очищеного звіту")
    parser.add_argument(
        "--check-conflicts", action="store_true", help="Перевіряти конфлікти правил"
    )
    parser.add_argument("--log-level", default="INFO", help="Рівень логування")

    args = parser.parse_args()
    run_analysis(args)


if __name__ == "__main__":
    main()
