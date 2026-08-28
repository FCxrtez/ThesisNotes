__all__ = ["adder_model"]


def __getattr__(name):
	if name == "adder_model":
		from .run_model import adder_model
		return adder_model
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")