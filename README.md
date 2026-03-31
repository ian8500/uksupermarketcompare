# BasketCompare (Phase 2)

This repository now includes a full phase-2 implementation with:

- Canonical product normalization service
- Pack-size parsing (`g`, `kg`, `ml`, `l`, `count`, multipacks)
- Confidence scoring (`exact`, `close`, `substitute`)
- Seeded supermarket datasets (Tesco, Sainsbury's, ASDA)
- Basket comparison algorithms:
  - cheapest basket overall
  - cheapest single-store basket
  - cheapest basket with own-brand substitutions
- Results UI payload including match reasoning
- Admin debug payload mapping raw vs canonical products
- Provider-based architecture for adding real providers later
- Unit tests with 30 realistic grocery parsing/matching cases

## Run tests

```bash
pytest
```
