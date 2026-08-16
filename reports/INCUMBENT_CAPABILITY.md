# What the incumbent standards can entail, and what they can reject

Generated 2026-08-16 by `pipeline/analyse_incumbents.py`. Every number below is counted directly from the published artefact named in the row.

## Axiom census

| Artefact | Triples | Classes | Object props | Datatype props | Entailing axioms | Refuting axioms | External alignments |
|---|---:|---:|---:|---:|---:|---:|---:|
| CEDS Ontology v14 (US Department of Education) | 243,601 | 967 | 0 | 0 | 1,381 | **24** | 1 |
| ASN schema (Achievement Standards Network) | 465 | 0 | 0 | 0 | 18 | **121** | 0 |
| LSO (this repository) | 440 | 19 | 16 | 24 | 12 | **100** | 0 |

*Refuting axioms* counts domains, ranges, disjointness, cardinality, functionality, irreflexivity, asymmetry and property disjointness: the axiom families that let data contradict the model. An artefact with none of them cannot be wrong about anything.


### CEDS Ontology v14 (US Department of Education)

- 243,601 triples, 967 `owl:Class`, 0 `owl:ObjectProperty`, 0 `owl:DatatypeProperty`, 2,336 bare `rdf:Property`.
- 19,546 `skos:Concept` across 966 `skos:ConceptScheme`; 965 terms are typed as BOTH `owl:Class` and `skos:ConceptScheme`.
- External alignments to any other vocabulary: **1**.
- Axioms present: `owl:allValuesFrom` 18, `rdfs:range` 6, `rdfs:subClassOf` 1,381.
- Axioms absent entirely: `owl:AllDisjointClasses`, `owl:AsymmetricProperty`, `owl:FunctionalProperty`, `owl:InverseFunctionalProperty`, `owl:IrreflexiveProperty`, `owl:SymmetricProperty`, `owl:TransitiveProperty`, `owl:cardinality`, `owl:complementOf`, `owl:disjointWith`, `owl:equivalentClass`, `owl:inverseOf`, `owl:maxCardinality`, `owl:minCardinality`, `owl:propertyDisjointWith`, `owl:someValuesFrom`, `rdfs:domain`, `rdfs:subPropertyOf`, `skos:broader`, `skos:narrower`.

### ASN schema (Achievement Standards Network)

- 465 triples, 0 `owl:Class`, 0 `owl:ObjectProperty`, 0 `owl:DatatypeProperty`, 57 bare `rdf:Property`.
- External alignments to any other vocabulary: **0**.
- Axioms present: `rdfs:domain` 62, `rdfs:range` 59, `rdfs:subClassOf` 2, `rdfs:subPropertyOf` 16.
- Axioms absent entirely: `owl:AllDisjointClasses`, `owl:AsymmetricProperty`, `owl:FunctionalProperty`, `owl:InverseFunctionalProperty`, `owl:IrreflexiveProperty`, `owl:SymmetricProperty`, `owl:TransitiveProperty`, `owl:allValuesFrom`, `owl:cardinality`, `owl:complementOf`, `owl:disjointWith`, `owl:equivalentClass`, `owl:inverseOf`, `owl:maxCardinality`, `owl:minCardinality`, `owl:propertyDisjointWith`, `owl:someValuesFrom`, `skos:broader`, `skos:narrower`.

### LSO (this repository)

- 440 triples, 19 `owl:Class`, 16 `owl:ObjectProperty`, 24 `owl:DatatypeProperty`, 0 bare `rdf:Property`.
- 0 `skos:Concept` across 2 `skos:ConceptScheme`; 0 terms are typed as BOTH `owl:Class` and `skos:ConceptScheme`.
- External alignments to any other vocabulary: **0**.
- Axioms present: `owl:AllDisjointClasses` 1, `owl:AsymmetricProperty` 1, `owl:FunctionalProperty` 15, `owl:IrreflexiveProperty` 1, `owl:TransitiveProperty` 1, `owl:equivalentClass` 2, `owl:maxCardinality` 1, `owl:someValuesFrom` 1, `rdfs:domain` 40, `rdfs:range` 40, `rdfs:subClassOf` 8, `rdfs:subPropertyOf` 1.
- Axioms absent entirely: `owl:InverseFunctionalProperty`, `owl:SymmetricProperty`, `owl:allValuesFrom`, `owl:cardinality`, `owl:complementOf`, `owl:disjointWith`, `owl:inverseOf`, `owl:minCardinality`, `owl:propertyDisjointWith`, `skos:broader`, `skos:narrower`.

### CASE package, Georgia Computer Science GSE (live)

- 2,453 CFItems, 2,483 CFAssociations.
- Association types: `isChildOf` 2,453, `isRelatedTo` 30.
- **98.8%** of associations are `isChildOf`, which is document structure rather than a correspondence between frameworks. Cross-framework associations (`exactMatchOf`, `isPeerOf`, `precedes`, `exemplar`): **0**.
- Items carrying a human coding scheme: 2,430; without: 23.
- CASE defines no logical axioms, so no assertion expressed in a CASE package can contradict the CASE specification. Its JSON schema constrains shape, not meaning.
