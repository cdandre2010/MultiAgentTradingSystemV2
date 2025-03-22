from neo4j import GraphDatabase

# Use Neo4j port 7689 for both Docker and Neo4j Desktop
uri = "bolt://localhost:7689"
username = "neo4j"
password = "SchoolsOut2025"

driver = GraphDatabase.driver(uri, auth=(username, password))
#driver = GraphDatabase.driver(uri)

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")
    print("Database cleared successfully!")

driver.close()