from collections import defaultdict
from contextvars import ContextVar
from functools import wraps

from django.db.models.sql import compiler
from django.db.backends.mysql import compiler as mysql_compiler

query_counts = ContextVar("query_counts", default=defaultdict(lambda: 0))

def reset_query_counter(**kwargs):
    query_counts.set(defaultdict(lambda: 0))


def count_queries(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        key = self.query.model._meta.label
        query_counts.get()[key] += 1
        return func(self, *args, **kwargs)
    return wrapper

def patch_sql_compilers_for_debugging():
    _SQLCompiler = compiler.SQLCompiler
    _SQLInsertCompiler = compiler.SQLInsertCompiler
    _SQLUpdateCompiler = compiler.SQLUpdateCompiler
    _SQLDeleteCompiler = compiler.SQLDeleteCompiler
    _SQLAggregateCompiler = compiler.SQLAggregateCompiler


    class DebugSQLCompiler(_SQLCompiler):
        @count_queries
        def execute_sql(self, *args, **kwargs):
            return super().execute_sql(*args, **kwargs)

    class DebugSQLInsertCompiler(_SQLInsertCompiler):
        @count_queries
        def execute_sql(self, *args, **kwargs):
            return super().execute_sql(*args, **kwargs)

    class DebugSQLUpdateCompiler(_SQLUpdateCompiler):
        @count_queries
        def execute_sql(self, *args, **kwargs):
            return super().execute_sql(*args, **kwargs)

    class DebugSQLDeleteCompiler(_SQLDeleteCompiler):
        @count_queries
        def execute_sql(self, *args, **kwargs):
            return super().execute_sql(*args, **kwargs)

    class DebugSQLAggregateCompiler(_SQLAggregateCompiler):
        @count_queries
        def execute_sql(self, *args, **kwargs):
            return super().execute_sql(*args, **kwargs)

    compiler.SQLCompiler = DebugSQLCompiler
    compiler.SQLInsertCompiler = DebugSQLInsertCompiler
    compiler.SQLUpdateCompiler = DebugSQLUpdateCompiler
    compiler.SQLDeleteCompiler = DebugSQLDeleteCompiler
    compiler.SQLAggregateCompiler = DebugSQLAggregateCompiler

    def unpatch():
        compiler.SQLCompiler = _SQLCompiler
        compiler.SQLInsertCompiler = _SQLInsertCompiler
        compiler.SQLUpdateCompiler = _SQLUpdateCompiler
        compiler.SQLDeleteCompiler = _SQLDeleteCompiler
        compiler.SQLAggregateCompiler = _SQLAggregateCompiler

    return unpatch
