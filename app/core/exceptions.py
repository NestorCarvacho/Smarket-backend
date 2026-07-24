"""Excepciones de dominio.

Los services lanzan estas excepciones sin conocer nada de HTTP. La capa de
API (routers + exception handlers en main.py) es la unica responsable de
traducirlas a codigos de estado HTTP. Esto respeta SRP: el dominio no sabe
que existe FastAPI.
"""


class DomainError(Exception):
    """Excepcion base de dominio."""


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class UnauthorizedError(DomainError):
    pass


class ForbiddenError(DomainError):
    pass
