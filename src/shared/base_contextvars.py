from contextvars import ContextVar

ctx_trace_id = ContextVar("ctx_trace_id", default=None)
ctx_caller_id = ContextVar("ctx_caller_id", default=None)