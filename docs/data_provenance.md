# Data provenance

Complete every bracketed field before publishing.

## Michigan

- Original source: `[source organization and dataset name]`
- Source URL: `[URL]`
- Retrieval date: `[YYYY-MM-DD]`
- Boundary vintage: `[year / enacted plan]`
- Unit of analysis: precincts
- District assignment field: `CD`
- Population field: `TOTPOP`
- Elections used: `PRE16D`, `PRE16R`, `PRE20D`, `PRE20R`
- Stored CRS: `EPSG:32616`
- Local path: `data/raw/mi/`
- Preprocessing: `[describe joins, repairs, dropped records, or graph bridges]`

## Missouri

- Original source: `[source organization and dataset name]`
- Source URL: `[URL]`
- Retrieval date: `[YYYY-MM-DD]`
- Boundary vintage: `[year / enacted plan]`
- Unit of analysis: precincts
- District assignment field: `CD`
- Population field: `TOTPOP`
- Elections used: `PRE16D`, `PRE16R`, `PRE20D`, `PRE20R`
- Stored CRS: `EPSG:32615`
- Local path: `data/raw/mo/`
- Preprocessing: `[describe joins, repairs, dropped records, or graph bridges]`

## Reproducibility notes

Do not claim that a new download is identical to the analyzed file unless checksums match. Before the final release, record SHA-256 hashes with:

```bash
shasum -a 256 data/raw/mi/mi/mi.shp data/raw/mi/mi/mi.dbf
shasum -a 256 data/raw/mo/mo/mo.shp data/raw/mo/mo/mo.dbf
```
