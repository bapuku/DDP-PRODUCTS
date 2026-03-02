// EU DPP Platform - Neo4j 5.x initial schema
// Constraints and indexes for knowledge graph (products, supply chain, regulations)
// EU AI Act Article 12 - compliance decisions traceable through graph

// ----- Constraints (idempotent) -----
CREATE CONSTRAINT product_gtin IF NOT EXISTS
FOR (p:Product) REQUIRE p.gtin IS UNIQUE;

CREATE CONSTRAINT supplier_eoid IF NOT EXISTS
FOR (s:Supplier) REQUIRE s.eoid IS UNIQUE;

CREATE CONSTRAINT batch_id IF NOT EXISTS
FOR (b:Batch) REQUIRE b.batch_id IS UNIQUE;

CREATE CONSTRAINT battery_passport_uri IF NOT EXISTS
FOR (bp:BatteryPassport) REQUIRE bp.dpp_uri IS UNIQUE;

CREATE CONSTRAINT regulation_celex IF NOT EXISTS
FOR (r:Regulation) REQUIRE r.celex_number IS UNIQUE;

CREATE CONSTRAINT regulatory_article_id IF NOT EXISTS
FOR (ra:RegulatoryArticle) REQUIRE (ra.celex_number, ra.article_number) IS UNIQUE;

// ----- Indexes for lookups -----
CREATE INDEX product_sector IF NOT EXISTS
FOR (p:Product) ON (p.sector);

CREATE INDEX product_manufacturing_date IF NOT EXISTS
FOR (p:Product) ON (p.manufacturing_date);

CREATE INDEX compliance_record_entity IF NOT EXISTS
FOR (c:ComplianceRecord) ON (c.entity_type, c.entity_id);

CREATE INDEX audit_entity IF NOT EXISTS
FOR (a:AuditLog) ON (a.entity_id);

// ----- Full-text search (compliance) -----
CREATE FULLTEXT INDEX compliance_search IF NOT EXISTS
FOR (n:ComplianceRecord) ON EACH [n.regulation, n.article, n.requirement_text];

// ----- Vector index for GraphRAG (Neo4j 5.x) -----
// RegulatoryClause nodes with embedding for semantic search (1536 dims)
CREATE VECTOR INDEX regulation_embeddings IF NOT EXISTS
FOR (r:RegulatoryClause) ON (r.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};
