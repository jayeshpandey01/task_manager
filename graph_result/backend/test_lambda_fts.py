import re
m_group_2 = 'almondd and yhme beard oil'
keywords = ' AND '.join([f"{k}~" for k in re.sub(r'[^\w\s]', '', m_group_2).split() if len(k) > 3])
query = f"CALL db.index.fulltext.queryNodes('product_fts', '{keywords}') YIELD node AS p MATCH (c:Customer)-[r1:PLACED]->(o:SalesOrder)-[r2:HAS_ITEM]->(i:SalesOrderItem)-[r3:IS_PRODUCT]->(p) RETURN c, r1, o, r2, i, r3, p"
print(query)
