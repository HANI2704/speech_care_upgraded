# MySQL Connection - supports both mysqlclient and PyMySQL
try:
    import MySQLdb  # noqa - mysqlclient installed
except ImportError:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass  # Neither installed - will raise error when DB is accessed
