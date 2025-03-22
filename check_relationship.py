from neo4j import GraphDatabase

uri = "bolt://localhost:7689"
username = "neo4j"
password = "SchoolsOut2025"

driver = GraphDatabase.driver(uri, auth=(username, password))

with driver.session() as session:
    result = session.run("MATCH (i:Instrument {symbol: 'BTCUSDT'})-[r]->(d:DataSourceType) RETURN type(r) as relationship_type")
    for record in result:
        print(record["relationship_type"])

driver.close()