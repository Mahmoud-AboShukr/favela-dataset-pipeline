# MapBiomas pilot selection for Brasília

## Selected raster
- Dataset: MapBiomas Coverage
- Year: 2024
- Territory downloaded: Brazil
- Source portal: MapBiomas
- Format: GeoTIFF
- Source file: `data/raw/mapbiomas/coverage_10m_2023/2024_coverage.tif`
- CRS: EPSG:4326
- Width: 167551
- Height: 144835
- Band count: 1
- Data type: uint8
- Nodata: 0
- Pixel size (degrees): 0.00026949458523585647 x 0.00026949458523585647
- Approximate ground resolution: ~30 m

## Important note on naming
The local folder name `coverage_10m_2023` appears inconsistent with the downloaded file metadata and filename (`2024_coverage.tif`). For documentation and downstream processing, the file metadata and filename should be treated as authoritative, not the local folder name. The raw data folder should be renamed later to avoid confusion.

## Intended use
This raster will be used as an auxiliary thematic layer for conservative refinement of Brasília favela polygons. The first pilot will use MapBiomas as a land-cover signal for vegetation removal and urban protection in a boundary-only refinement workflow.

## Initial class policy

### Remove candidates
Vegetation-like classes to be treated as removal candidates in the first pilot:
- Forest Formation
- Wooded Sandbank Vegetation
- Floodable Forest
- Mangrove
- Savanna Formation
- Grassland Formation
- Herbaceous Sandbank Vegetation
- Wetland

### Keep / protect
Strong built-support class to preserve in the first pilot:
- Urban Area

### Optional forced removal
Water-like classes that may be used as forced removal if needed:
- River, Lake and Ocean
- Aquaculture

### Ignore / uncertain
Ambiguous or mixed classes that will remain unchanged in the first pilot:
- Pasture
- Agriculture
- Mosaic of Uses
- Other Non Vegetated Areas
- Mining
- Not Observed
- Rocky Outcrop
- other mixed or ambiguous classes

### Bare soil decision
- Bare soil / exposed non-vegetated surfaces are treated as ignore/uncertain in v1.
- They will not be used as automatic removal.
- They will not be used as hard keep/protect.
- They will remain unchanged in the first conservative refinement pass.

## Operational taxonomy
- Vegetation -> candidate for removal
- Urban -> keep/protect
- Water -> optional forced removal
- Everything else -> uncertain

## Notes
This first taxonomy is intentionally conservative. The objective is to support boundary-only refinement of favela polygons rather than full polygon redrawing. The full categorical raster is retained as the source of truth, and binary masks will be derived from class codes in later steps.