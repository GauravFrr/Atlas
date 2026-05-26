from modules.outreach.cold_email import ColdEmailEngine

__all__ = ["ColdEmailEngine", "Manager"]


def __getattr__(name: str):
    if name == "Manager":
        from modules.outreach.manager import Manager

        return Manager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
