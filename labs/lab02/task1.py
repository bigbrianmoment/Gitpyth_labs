import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import ClassVar

# Кількість ітерацій для PBKDF2. Винесено в константу, щоб легко
# змінювати значення в одному місці.
PBKDF2_ITERATIONS = 100_000

# Розмір солі в байтах
SALT_SIZE = 16

# Таймаут сесії за замовчуванням (у секундах)
SESSION_TIMEOUT_SEC = 900

# Регулярний вираз для перевірки email. Локальна частина починається
# з латинської літери, 3-64 символи (літери, цифри, підкреслення),
# далі @ і доменне ім'я з хоча б однією крапкою.
EMAIL_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{2,63}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class User:
    """Базовий клас користувача з безпечним зберіганням пароля."""

    def __init__(self, username: str, email: str, role: str = "user"):
        self.username = username
        self.email = email  # проходить через property-сеттер нижче
        self.role = role
        self.active = True

        # Приватні атрибути (name mangling: _User__password_hash)
        self.__password_hash = None
        self.__password_salt = None

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not EMAIL_PATTERN.match(value):
            raise ValueError(f"Некоректний формат email: {value}")
        self._email = value

    def set_password(self, password: str) -> None:
        """Генерує нову сіль і зберігає хеш пароля. Сам пароль ніде не зберігається."""
        salt = os.urandom(SALT_SIZE)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
        )
        self.__password_salt = salt
        self.__password_hash = password_hash

    def check_password(self, password: str) -> bool:
        """Перевіряє пароль, порівнюючи хеші через compare_digest
        (захист від атак по часу виконання)."""
        if self.__password_hash is None or self.__password_salt is None:
            return False

        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), self.__password_salt, PBKDF2_ITERATIONS
        )
        return hmac.compare_digest(candidate_hash, self.__password_hash)

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        status = "active" if self.active else "inactive"
        return f"User(username={self.username}, role={self.role}, status={status})"


class Admin(User):
    """Адміністратор. Успадковує User і додає систему дозволів."""

    def __init__(self, username: str, email: str, permissions=None):
        # super() викликає конструктор батьківського класу User
        super().__init__(username, email, role="admin")

        # Не задаємо змінювану колекцію типовим аргументом (def __init__(self, permissions=[])
        # створила б одну спільну колекцію для всіх об'єктів). Замість цього
        # перевіряємо None і створюємо нову колекцію всередині методу.
        self.permissions = set(permissions) if permissions else set()

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        perms = ", ".join(sorted(self.permissions)) if self.permissions else "none"
        return f"Admin(username={self.username}, permissions=[{perms}])"


class Session:
    """Сесія користувача з часом входу та останньої активності."""

    def __init__(self, ip: str):
        self.ip = ip
        self.login_time = datetime.now(timezone.utc)
        self.last_activity = self.login_time

    def touch(self) -> None:
        """Оновлює час останньої активності до поточного моменту."""
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        """Перевіряє, чи не минув термін дії сесії."""
        if timeout_sec <= 0:
            raise ValueError("timeout_sec повинен бути додатним числом")

        elapsed = datetime.now(timezone.utc) - self.last_activity
        return elapsed < timedelta(seconds=timeout_sec)


@dataclass
class AuditRecord:
    """Один запис аудиту. @dataclass автоматично генерує __init__,
    __repr__ та __eq__, тому не треба писати їх вручну для простої
    структури даних."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Зберігає історію подій безпеки (вхід, вихід, помилки входу)."""

    def __init__(self):
        self._records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        record = AuditRecord(
            timestamp=datetime.now(timezone.utc), username=username, action=action
        )
        self._records.append(record)

    def show_all(self) -> None:
        for record in self._records:
            ts = record.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"  [{ts}] {record.username}: {record.action}")


class UserAccount:
    """Об'єднує User, Session та AuditLog через композицію
    (UserAccount МАЄ User і Session, а не є ними)."""

    # Дозволені ключі для __getitem__ / __setitem__
    _ALLOWED_KEYS: ClassVar[set[str]] = {"user", "session", "audit_log"}

    def __init__(self, user: User, audit_log: AuditLog = None):
        self.user = user
        self.session: Session | None = None
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        """Перевіряє логін і пароль, створює сесію лише при успіху."""
        if not self.user.active or self.user.username != username:
            self.audit_log.add_log(username, "login_failure")
            return False

        if not self.user.check_password(password):
            self.audit_log.add_log(username, "login_failure")
            return False

        self.session = Session(ip)
        self.session.touch()
        self.audit_log.add_log(username, "login_success")
        return True

    def is_authenticated(self) -> bool:
        """Перевіряє, чи є активна сесія. Невдала перевірка
        не подовжує термін дії сесії (тобто не викликає touch())."""
        if self.session is None:
            return False
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        if self.session is not None:
            self.audit_log.add_log(self.user.username, "logout")
            self.session = None

    def __getitem__(self, key: str):
        if key not in self._ALLOWED_KEYS:
            raise KeyError(f"Невідомий ключ: {key}")
        return getattr(self, key)

    def __setitem__(self, key: str, value) -> None:
        if key not in self._ALLOWED_KEYS:
            raise KeyError(f"Невідомий ключ: {key}")

        if key == "user" and not isinstance(value, User):
            raise TypeError("Значення для 'user' повинно бути екземпляром User")
        if key == "session" and value is not None and not isinstance(value, Session):
            raise TypeError("Значення для 'session' повинно бути екземпляром Session")
        if key == "audit_log" and not isinstance(value, AuditLog):
            raise TypeError(
                "Значення для 'audit_log' повинно бути екземпляром AuditLog"
            )

        setattr(self, key, value)
