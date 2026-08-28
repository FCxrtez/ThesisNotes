__all__ = ["adder_golden_model"]


def __getattr__(name):
	if name == "adder_golden_model":
		from .run_golden_model import adder_golden_model
		return adder_golden_model
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")