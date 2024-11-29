from collections import defaultdict
from contextvars import ContextVar
from functools import wraps

from django.db.models.sql import compiler
from django.db.backends.mysql import compiler as mysql_compiler

query_counts = ContextVar("query_counts", default=defaultdict(int))


def reset_query_counter(**kwargs):
    query_counts.set(defaultdict(int))


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
    _MySQLCompiler = mysql_compiler.SQLCompiler
    _MySQLInsertCompiler = mysql_compiler.SQLInsertCompiler
    _MySQLUpdateCompiler = mysql_compiler.SQLUpdateCompiler
    _MySQLDeleteCompiler = mysql_compiler.SQLDeleteCompiler
    _MySQLAggregateCompiler = mysql_compiler.SQLAggregateCompiler

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

    class DebugMySQLCompiler(_MySQLCompiler):
        @count_queries
        def execute_sql(self, *args, **kwargs):
            return super().execute_sql(*args, **kwargs)

    class DebugMySQLInsertCompiler(_MySQLInsertCompiler):
        @count_queries
        def execute_sql(self, *args, **kwargs):
            return super().execute_sql(*args, **kwargs)

    class DebugMySQLUpdateCompiler(_MySQLUpdateCompiler):
        @count_queries
        def execute_sql(self, *args, **kwargs):
            return super().execute_sql(*args, **kwargs)

    class DebugMySQLDeleteCompiler(_MySQLDeleteCompiler):
        @count_queries
        def execute_sql(self, *args, **kwargs):
            return super().execute_sql(*args, **kwargs)

    class DebugMySQLAggregateCompiler(_MySQLAggregateCompiler):
        @count_queries
        def execute_sql(self, *args, **kwargs):
            return super().execute_sql(*args, **kwargs)

    compiler.SQLCompiler = DebugSQLCompiler
    compiler.SQLInsertCompiler = DebugSQLInsertCompiler
    compiler.SQLUpdateCompiler = DebugSQLUpdateCompiler
    compiler.SQLDeleteCompiler = DebugSQLDeleteCompiler
    compiler.SQLAggregateCompiler = DebugSQLAggregateCompiler
    mysql_compiler.SQLCompiler = DebugMySQLCompiler
    mysql_compiler.SQLInsertCompiler = DebugMySQLInsertCompiler
    mysql_compiler.SQLUpdateCompiler = DebugMySQLUpdateCompiler
    mysql_compiler.SQLDeleteCompiler = DebugMySQLDeleteCompiler
    mysql_compiler.SQLAggregateCompiler = DebugMySQLAggregateCompiler

    def unpatch():
        compiler.SQLCompiler = _SQLCompiler
        compiler.SQLInsertCompiler = _SQLInsertCompiler
        compiler.SQLUpdateCompiler = _SQLUpdateCompiler
        compiler.SQLDeleteCompiler = _SQLDeleteCompiler
        compiler.SQLAggregateCompiler = _SQLAggregateCompiler
        mysql_compiler.SQLCompiler = _MySQLCompiler
        mysql_compiler.SQLInsertCompiler = _MySQLInsertCompiler
        mysql_compiler.SQLUpdateCompiler = _MySQLUpdateCompiler
        mysql_compiler.SQLDeleteCompiler = _MySQLDeleteCompiler
        mysql_compiler.SQLAggregateCompiler = _MySQLAggregateCompiler

    return unpatch
