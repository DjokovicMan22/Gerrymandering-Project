from pathlib import Path
import zipfile

import geopandas
import matplotlib.pyplot as plt


project_root = Path(__file__).resolve().parents[1]

zip_path = project_root / "data" / "raw" / "mo.zip"

extract_folder = project_root / "data" / "raw" / "mo"

if not zip_path.exists():
    raise FileNotFoundError(f"Could not find: {zip_path}")

extract_folder.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as zip_file:
    zip_file.extractall(extract_folder)

shapefiles = list(extract_folder.rglob("*.shp"))

if not shapefiles:
    raise FileNotFoundError("No .shp file found after extracting mi.zip")

shapefile_path = shapefiles[0]

print(f"Found shapefile: {shapefile_path}")

missouri = geopandas.read_file(shapefile_path)

print("\nLoaded successfully.")
print(f"Number of rows: {len(missouri)}")

print("\nColumns:")
print(missouri.columns.tolist())

if "PRE20D" in missouri.columns and "PRE20R" in missouri.columns:

    total_two_party_votes = missouri["PRE20D"] + missouri["PRE20R"]

    missouri["dem_share"] = (
        missouri["PRE20D"] / total_two_party_votes
    )

    missouri.plot(
        column="dem_share",
        cmap="RdBu",
        legend=True,
        figsize=(10, 10),
        vmin=0,
        vmax=1,
    )

    plt.title("Missouri 2020 Democratic Two-Party Vote Share")
    plt.axis("off")
    plt.show()

else:
    print(
        "\nThe file loaded, but PRE20D and PRE20R were not found."
    )
    print(
        "Look at the printed column names to identify the correct vote columns."
    )