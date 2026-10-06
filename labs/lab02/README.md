Варіант 3 - "Валідатор та аналізатор конфігурацій правил фаєрвола"
pip install -r requirements.txt
[
  {
    "id": 1,
    "source": "10.0.0.0/8",
    "destination": "192.168.10.10",
    "port": "443",
    "action": "ALLOW"
  },
  {
    "id": 2,
    "source": "10.0.0.0/8",
    "destination": "192.168.10.10",
    "port": "443",
    "action": "ALLOW"
  },
  {
    "id": 3,
    "source": "10.0.0.0/8",
    "destination": "192.168.10.10",
    "port": "443",
    "action": "DENY"
  },
  {
    "id": 4,
    "source": "0.0.0.0/0",
    "destination": "192.168.10.20",
    "port": "22",
    "action": "ALLOW"
  },
  {
    "id": 5,
    "source": "192.168.1.0/24",
    "destination": "10.10.0.5",
    "port": "ANY",
    "action": "ALLOW"
  },
  {
    "id": 6,
    "source": "172.16.5.10",
    "destination": "10.10.0.10",
    "port": "53",
    "action": "ALLOW"
  },
  {
    "id": 7,
    "source": "172.16.5.10",
    "destination": "10.10.0.10",
    "port": "53",
    "action": "DENY"
  },
  {
    "id": 8,
    "source": "999.10.1.1",
    "destination": "10.10.0.11",
    "port": "80",
    "action": "ALLOW"
  },
  {
    "id": 9,
    "source": "192.168.2.0/33",
    "destination": "10.10.0.12",
    "port": "443",
    "action": "DENY"
  },
  {
    "id": 10,
    "source": "192.168.3.15",
    "destination": "300.1.1.1",
    "port": "25",
    "action": "ALLOW"
  },
  {
    "id": 11,
    "source": "203.0.113.0/24",
    "destination": "192.168.10.50",
    "port": "3389",
    "action": "DENY"
  },
  {
    "id": 12,
    "source": "198.51.100.7",
    "destination": "192.168.10.51",
    "port": "8080",
    "action": "ALLOW"
  },
  {
    "id": 13,
    "source": "0.0.0.0/0",
    "destination": "192.168.10.99",
    "port": "ANY",
    "action": "ALLOW"
  },
  {
    "id": 14,
    "source": "10.20.30.40",
    "destination": "192.168.50.1",
    "port": "22",
    "action": "BLOCK"
  }
]

python -m labs.lab02.main demo

=== Демонстрація Завдання 1: User, Admin, Session, AuditLog ===

1. Успішний вхід:
   login('John', правильний пароль) -> True
   is_authenticated() -> True

2. Невдалий вхід (неправильний пароль):
   login('Joe', неправильний пароль) -> False

3. Зміна email:
   Поточний email: doe@example.com
   Новий email встановлено: new_John@example.com
   Спроба встановити некоректний email -> ValueError: Некоректний формат email: некоректний-email

4. Права адміністратора:
   Admin(username=admin_bob, permissions=[manage_users, view_audit_log])
   has_permission('manage_users') -> True
   Після revoke_permission('manage_users'): Admin(username=admin_bob, permissions=[view_audit_log])

5. Завершення сесії за таймаутом:
   Одразу після входу, is_authenticated() -> True
   Після імітації простою (1000 сек), is_authenticated() -> False

6. Вихід із системи:
   Після logout(), is_authenticated() -> False

7. Журнал подій (AuditLog):
  [2026-10-06 20:48:33 UTC] John: login_success
  [2026-10-06 20:48:33 UTC] John: logout
  [2026-10-06 20:48:33 UTC] John: login_failure
  [2026-10-06 20:48:33 UTC] John: login_success
  [2026-10-06 20:48:33 UTC] John: logout

python -m labs.lab02.task2 --rules-file labs/lab02/data/firewall_rules.json --check-conflicts --output labs/lab02/data/fw_audit_report.json

[INFO] Parsing firewall rules from labs/lab02/data/firewall_rules.json...
[INFO] Total rules parsed: 14. Validating IP syntax and rule logic...
[WARNING] Rule #8 rejected: invalid source IP: 999.10.1.1
[WARNING] Rule #9 rejected: invalid source IP: 192.168.2.0/33
[WARNING] Rule #10 rejected: invalid destination IP: 300.1.1.1
[WARNING] Rule #14 rejected: invalid action: BLOCK

=== Firewall Configuration Audit Report ===
Invalid IP/Port/Action Entries : 4
Conflicting Rules              : 2 conflicts found
Duplicate Rules                 : 1 duplicates found
High-Risk Rules                 : 3 dangerous ALLOW ALL rules

=== Critical Findings ===
[INVALID] Rule #8: invalid source IP: 999.10.1.1
[INVALID] Rule #9: invalid source IP: 192.168.2.0/33
[INVALID] Rule #10: invalid destination IP: 300.1.1.1
[INVALID] Rule #14: invalid action: BLOCK
[CONFLICT] ALLOW rules (#1, #2) conflict with DENY rules (#3) for 10.0.0.0/8 -> 192.168.10.10:443
[CONFLICT] ALLOW rules (#6) conflict with DENY rules (#7) for 172.16.5.10 -> 10.10.0.10:53
[DUPLICATE] Rules #1, #2 are identical: ALLOW 10.0.0.0/8 -> 192.168.10.10:443
[HIGH-RISK] Rule #4: ALLOW 0.0.0.0/0 -> 192.168.10.20:22 (Source: 0.0.0.0/0)
[HIGH-RISK] Rule #5: ALLOW 192.168.1.0/24 -> 10.10.0.5:ANY (Port: ANY)
[HIGH-RISK] Rule #13: ALLOW 0.0.0.0/0 -> 192.168.10.99:ANY (Port: ANY)
[INFO] Security report successfully exported to labs/lab02/data/fw_audit_report.json

CLI

--rules-file	обов'язковий	шлях до JSON файлу з правилами фаєрвола
--output	не обов'язковий 	шлях, куди зберегти очищений список коректних правил
--check-conflicts	прапорець	вмикає пошук дублікатів і суперечливих правил
--log-level	не обов'язковий, за замовчуванням INFO	рівень деталізації логів: DEBUG, INFO, WARNING, ERROR

Поведінка при помилках

Якщо файл правил не знайдено, програма виводить повідомлення рівня ERROR і завершується з кодом виходу 1. Те саме відбувається, якщо файл містить некоректний JSON або немає прав на читання файлу.
Окремі правила з некоректним форматом IP адреси, маски, порту або дії не зупиняють роботу всієї програми. Кожне таке правило позначається попередженням у логах і виключається з подальшого аналізу та з підсумкового файлу збережених правил.
Поведінка при помилках
Якщо файл правил не знайдено, програма виводить повідомлення рівня ERROR і завершується з кодом виходу 1. Те саме відбувається, якщо файл містить некоректний JSON або немає прав на читання файлу.
Окремі правила з некоректним форматом IP адреси, маски, порту або дії не зупиняють роботу всієї програми. Кожне таке правило позначається попередженням у логах і виключається з подальшого аналізу та з підсумкового файлу збережених правил.