# Sentinel-1 Preprocessing (SAR)

Sentinel-1 SAR provides cloud-robust information complementary to optical inputs.

---

## 1. Product selection
- GRD products are commonly used for large-scale mapping.
- Polarizations: **VV, VH** (default).

---

## 2. Standard preprocessing chain
The typical SAR preprocessing steps are:

1) Apply orbit file (if required by toolchain)
2) Radiometric calibration (to sigma0 or gamma0)
3) Speckle filtering (optional; can blur edges—use cautiously)
4) Terrain correction (orthorectification using a DEM)
5) Convert to dB scale (optional but common):
   - `10 * log10(value)`

---

## 3. Feature construction (optional)
In addition to VV and VH, you may include derived features:
- VV/VH ratio
- VV - VH difference
- texture measures (if justified)

These features must be documented and treated consistently across splits.

---

## 4. Alignment and resampling
- Sentinel-1 processed outputs must be resampled to the master grid (typically Sentinel-2 10 m).
- Resampling method:
  - continuous SAR intensity/backscatter: bilinear (or cubic in some cases)
- Alignment checks:
  - same CRS, shape, transform as S2 and label masks.

---

## 5. Outputs
Recommended outputs per AOI/state:
- `data/processed/<aoi_or_state>/s1/<state>_s1_stack.tif` (VV, VH, optional derived channels)