from dataclasses import dataclass


@dataclass
class User:
    """Represents a user."""

    name: str
    age: int

    def is_adult(self) -> bool:
        """Check if user is an adult."""
        return self.age >= 18

    def greet(self, greeting: str = "Hello") -> str:
        """Return a greeting message."""
        return f"{greeting}, {self.name}!"


class Admin(User):
    """An admin user with elevated privileges."""

    role: str = "admin"

    def has_permission(self, action: str) -> bool:
        """Check if admin has permission for an action."""
        return True
