# MapBiomas boundary-ring QC summary

- Input raster: `data/interim/mapbiomas_clips/mapbiomas_brasilia_aoi_clip.tif`
- Favela polygons: `data/interim/polygons_clean/favelas_brasilia.gpkg`
- Ring width: `120.0 m`
- Number of polygons inspected: `70`

## Global zone composition
- Full polygons: urban 73.8554%, vegetation 17.7083%, uncertain 8.3821%, water 0.0542%
- Core: urban 0.0%, vegetation 0.0%, uncertain 0.0%, water 0.0%
- Ring: urban 0.0%, vegetation 0.0%, uncertain 0.0%, water 0.0%

## Spatial QC signals
- Polygons where ring vegetation > core vegetation: 0 / 70
- Polygons where core urban > ring urban: 0 / 70

## Interpretation
A conservative boundary-only refinement is more plausible if vegetation is systematically stronger in the ring and urban support is systematically stronger in the core.

## High-risk polygons to inspect manually
- Polygons with non-empty core after 120 m inward buffer: 44 / 70
- None flagged by the current heuristic.

## Generated figures
- `figures/mapbiomas_zone_composition.png`
- `figures/mapbiomas_ring_vs_core_vegetation.png`
- `figures/mapbiomas_ring_vs_core_urban.png`