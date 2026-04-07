# 2026-03-26 — Imagery Acquisition Policy

## Purpose

This note fixes the acquisition policy for the first version of the Sentinel imagery pipeline that will support the refined favela polygons.

The goal is to build a reproducible and scalable workflow for downloading and preparing Sentinel-1 and Sentinel-2 imagery for the year 2022, starting with one pilot city and later extending to additional cities.

---

## Scope

This policy applies to the first implementation of the imagery pipeline for:

- Sentinel-2 optical imagery
- Sentinel-1 radar imagery
- year 2022 only
- AOI-based acquisition and processing
- first pilot city: Manaus

---

## Temporal Policy

To remain consistent with the other data sources already adopted in the project, all imagery for this stage will be limited to the 2022 calendar year.

### Date range

- start date: `2022-01-01`
- end date: `2022-12-31`

---

## Pilot AOI Policy

The first city to process and validate is:

- **Manaus**

Reason:
- Manaus is already the current pilot city in the refined polygon workflow
- it is a difficult and useful test case because of strong vegetation interaction and challenging urban edges
- validating the imagery workflow there first reduces the risk of scaling errors later

---

## Sentinel-2 Policy

### Product

Use:

- **Sentinel-2 Level-2A (L2A)**

Reason:
- L2A is the atmospherically corrected surface reflectance product
- it is more appropriate than rawer products for land-cover and urban analysis
- it includes the Scene Classification Layer (SCL), which is useful for cloud and cloud-shadow masking

### Initial metadata filter

For the first version, use:

- `eo:cloud_cover <= 40`

Reason:
- a strict `0%` filter is too restrictive
- cloud metadata is scene-level/tile-level, not AOI-specific
- a scene with non-zero cloud cover can still be usable over the city
- cloud removal will be handled later at pixel level using SCL-based masks

### Cloud masking baseline

For the first implementation, cloud and cloud-shadow masking will use:

- **SCL (Scene Classification Layer)**

Possible later refinement:
- add **s2cloudless** if SCL alone is not sufficient

### Sentinel-2 final output

For each AOI, the first required optical output is:

- `s2_2022_composite.tif`

This will be a cloud-reduced 2022 composite, initially built as an annual composite.

---

## Sentinel-1 Policy

### Product

Use:

- **Sentinel-1 GRD**

Reason:
- Sentinel-1 is radar imagery and is not blocked by cloud cover
- it is useful for building a stable yearly radar summary over the AOI
- it complements Sentinel-2 in cloudy and humid environments

### Polarizations

Keep:

- **VV**
- **VH**

### Sentinel-1 final outputs

For each AOI, the required radar outputs are:

- `s1_2022_vv_median.tif`
- `s1_2022_vh_median.tif`

Optional later output:

- `s1_2022_vv_vh_ratio.tif`

These outputs will be yearly summary rasters built from all selected 2022 acquisitions.

---

## Processing Strategy

### Sentinel-2

The workflow will be:

1. search 2022 Sentinel-2 L2A scenes intersecting the AOI
2. apply initial metadata filtering
3. build cloud/cloud-shadow masks using SCL
4. remove invalid pixels
5. combine valid observations into one 2022 optical composite

### Sentinel-1

The workflow will be:

1. search 2022 Sentinel-1 GRD scenes intersecting the AOI
2. select scenes with the required polarizations
3. build yearly radar stacks
4. compute summary rasters such as VV median and VH median

---

## Spatial Alignment Policy

All final outputs must be aligned to a common grid.

### Master grid

For the first version, use:

- **the final Sentinel-2 10 m output grid as the master grid**

This means the final Sentinel-1 outputs will later be aligned to the Sentinel-2 reference grid.

### Alignment requirements

All final imagery outputs must share:

- the same CRS
- the same resolution
- the same pixel alignment
- the same extent logic for the AOI

---

## Repository Policy

The imagery workflow will remain inside the same project repository.

Reason:
- it directly supports the refined favela polygons
- it uses the same AOIs and project structure
- it simplifies downstream quality control and dataset creation
- it avoids duplication of code, folders, and metadata

### Planned code location

- `src/imagery/`

### Planned data locations

- `data/raw/sentinel1/`
- `data/raw/sentinel2/`
- `data/interim/imagery/sentinel1/`
- `data/interim/imagery/sentinel2/`
- `data/processed/imagery/`

---

## First Implementation Priority

The implementation order is:

1. create repository structure
2. implement Sentinel-2 search and download for Manaus
3. inspect available scenes and metadata
4. implement Sentinel-1 search and download for Manaus
5. build the Sentinel-2 cloud-mask step
6. build the 2022 Sentinel-2 composite
7. build the 2022 Sentinel-1 yearly summaries
8. align all final outputs
9. validate in QGIS
10. scale to additional cities

---

## Expected First Deliverables

For the Manaus pilot, the first target outputs are:

- `s2_2022_composite.tif`
- `s1_2022_vv_median.tif`
- `s1_2022_vh_median.tif`

Optional:
- `s1_2022_vv_vh_ratio.tif`

---

## Status

Policy fixed on:

- `2026-03-26`

Current status:

- acquisition policy defined
- repository structure to be created next
- Sentinel-2 search/download script to be implemented first