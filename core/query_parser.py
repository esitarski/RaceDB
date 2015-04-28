import sqlparse
sql = 'select * from foo where City not like "ON%" and price > 100;'
print sqlparse.format(sql, reindent=True, keyword_case='upper')

parsed = sqlparse.parse( sql )
print parsed

stmt = parsed[0]
print stmt.tokens