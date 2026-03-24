import geopandas as gpd
import pandas as pd
from pathlib import Path

# Paths
favelas_path = Path("data/raw/favelas_shp/favelas.shp")
munis_path = Path("data/raw/ibge/BR_Municipios_2024/BR_Municipios_2024.shp")

# Load
favelas = gpd.read_file(favelas_path)
munis = gpd.read_file(munis_path)

# Reproject if needed
if favelas.crs != munis.crs:
    favelas = favelas.to_crs(munis.crs)

# -------------------------------------------------------------------
# IMPORTANT:
# Adjust these column names to match your IBGE layer exactly.
# Common possibilities are:
# - state code/name: "SIGLA_UF", "NM_UF"
# - municipality name: "NM_MUN"
# -------------------------------------------------------------------

state_col = "SIGLA_UF"
muni_col = "NM_MUN"

# Brazil state capitals
capitals = {
    "AC": "Rio Branco",
    "AL": "Maceió",
    "AP": "Macapá",
    "AM": "Manaus",
    "BA": "Salvador",
    "CE": "Fortaleza",
    "DF": "Brasília",
    "ES": "Vitória",
    "GO": "Goiânia",
    "MA": "São Luís",
    "MT": "Cuiabá",
    "MS": "Campo Grande",
    "MG": "Belo Horizonte",
    "PA": "Belém",
    "PB": "João Pessoa",
    "PR": "Curitiba",
    "PE": "Recife",
    "PI": "Teresina",
    "RJ": "Rio de Janeiro",
    "RN": "Natal",
    "RS": "Porto Alegre",
    "RO": "Porto Velho",
    "RR": "Boa Vista",
    "SC": "Florianópolis",
    "SP": "São Paulo",
    "SE": "Aracaju",
    "TO": "Palmas",
}

# Filter municipality polygons to state capitals
capital_rows = []
for uf, cap_name in capitals.items():
    sub = munis[(munis[state_col] == uf) & (munis[muni_col] == cap_name)].copy()
    if len(sub) == 0:
        print(f"Warning: could not find capital for {uf} - {cap_name}")
    capital_rows.append(sub)

capitals_gdf = pd.concat(capital_rows, ignore_index=True)
capitals_gdf = gpd.GeoDataFrame(capitals_gdf, geometry="geometry", crs=munis.crs)

# Spatial join: favela polygons intersecting a capital municipality
joined = gpd.sjoin(
    favelas,
    capitals_gdf[[state_col, muni_col, "geometry"]],
    how="inner",
    predicate="intersects"
).drop(columns=["index_right"], errors="ignore")

# If a polygon touches more than one municipality for any reason, keep unique polygon ids
# Adjust the polygon id field if needed
favela_id_col = None
for c in ["id", "ID", "fid", "FID"]:
    if c in favelas.columns:
        favela_id_col = c
        break

if favela_id_col is None:
    # fallback: use the dataframe index as unique id
    favelas = favelas.reset_index().rename(columns={"index": "_tmp_id"})
    joined = joined.reset_index().rename(columns={"index": "_tmp_id"})
    favela_id_col = "_tmp_id"

total_polygons = len(favelas)
capital_polygons = joined[favela_id_col].nunique()
percentage = 100 * capital_polygons / total_polygons

# Per-capital counts
per_capital = (
    joined.groupby([state_col, muni_col])[favela_id_col]
    .nunique()
    .reset_index(name="favela_polygon_count")
    .sort_values("favela_polygon_count", ascending=False)
)

print("\n=== NATIONAL SUMMARY ===")
print(f"Total favela polygons in Brazil: {total_polygons}")
print(f"Favela polygons in state capital municipalities: {capital_polygons}")
print(f"Percentage in state capitals: {percentage:.2f}%")

print("\n=== PER CAPITAL ===")
print(per_capital.to_string(index=False))

# Optional save
out_csv = Path("data/processed/final_pipeline/capital_polygon_counts.csv")
out_csv.parent.mkdir(parents=True, exist_ok=True)
per_capital.to_csv(out_csv, index=False)
print(f"\nSaved per-capital counts to: {out_csv}")