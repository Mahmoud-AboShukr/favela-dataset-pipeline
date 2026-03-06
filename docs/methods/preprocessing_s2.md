# Sentinel-2 Preprocessing (Optical)

This document describes the preprocessing steps planned/used for Sentinel-2 imagery before training segmentation models.

---

## 1. Product selection
- Level: **L2A (Surface Reflectance)** preferred.
- Rationale: surface reflectance is more stable across time and location than top-of-atmosphere reflectance.

---

## 2. Band selection
### Core 10 m bands (default)
- B02 (Blue)
- B03 (Green)
- B04 (Red)
- B08 (NIR)

These provide a strong baseline for urban/built-up segmentation.

### Optional 20 m bands (if used)
- B11, B12 (SWIR)

If included, they must be resampled to 10 m to match the master grid.

---

## 3. Cloud handling
Clouds and cloud shadows must be handled to prevent label/input mismatch and training noise.

### Preferred method
- Use SCL (Scene Classification Layer) from L2A products.

### Policy (configurable)
- Maximum allowed cloud percentage for scene selection (e.g., 20%).
- If no sufficiently clear image exists:
  - use compositing (median) over a date range.

---

## 4. Compositing (if needed)
Two options:
1) **Single best scene**
- choose lowest cloud cover within date window

2) **Median composite**
- compute median reflectance per pixel from multiple dates after masking clouds

---

## 5. Radiometric normalization (optional)
Depending on model sensitivity:
- scale reflectance to [0,1] or standardize per band (mean/std).
- Any normalization must be consistent across train/val/test and documented.

---

## 6. Resampling and alignment
Final images must match the master grid (typically Sentinel-2 10 m):
- CRS, transform, resolution, extent must match masks exactly.
- Resampling:
  - continuous reflectance: bilinear
  - categorical layers (SCL): nearest

---

## 7. Outputs
Recommended outputs per AOI/state:
- stacked GeoTIFF (bands as channels) aligned to master grid:
  - `data/processed/<aoi_or_state>/s2/<state>_s2_stack.tif`
- optional cloud mask:
  - `data/processed/<aoi_or_state>/s2/<state>_cloudmask.tif`