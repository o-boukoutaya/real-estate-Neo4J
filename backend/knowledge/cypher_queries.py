# Quelques requêtes utilitaires
GET_ALL_NODES = "MATCH (n) RETURN n LIMIT 25"
COUNT_CHUNKS = "MATCH (c:Chunk) RETURN count(c) AS cnt"