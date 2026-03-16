import rasterio

# path = r".\data\raw\mapbiomas\coverage_10m_2023\2024_coverage.tif"
path = r"data/interim/masks/brasilia_mapbiomas_vegetation_mask_strict.tif"

with rasterio.open(path) as src:
    print("path:", path)
    print("crs:", src.crs)
    print("width:", src.width)
    print("height:", src.height)
    print("count:", src.count)
    print("dtype:", src.dtypes)
    print("nodata:", src.nodata)
    print("transform:", src.transform)
    print("res:", src.res)