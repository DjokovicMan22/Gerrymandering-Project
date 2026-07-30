from pathlib import Path
import zipfile

import geopandas
import matplotlib.pyplot as plt


# Find the project root.
# This assumes this file is inside the scripts folder.
project_root = Path(__file__).resolve().parents[1]

# Location of the downloaded ZIP file.
zip_path = project_root / "data" / "raw" / "mi.zip"

# Folder where the ZIP contents will be extracted.
extract_folder = project_root / "data" / "raw" / "mi"


# 1. Make sure the ZIP exists.
if not zip_path.exists():
    raise FileNotFoundError(f"Could not find: {zip_path}")


# 2. Extract the ZIP.
extract_folder.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as zip_file:
    zip_file.extractall(extract_folder)


# 3. Find the shapefile automatically.
shapefiles = list(extract_folder.rglob("*.shp"))

if not shapefiles:
    raise FileNotFoundError("No .shp file found after extracting mi.zip")

shapefile_path = shapefiles[0]

print(f"Found shapefile: {shapefile_path}")


# 4. Load the shapefile with GeoPandas.
michigan = geopandas.read_file(shapefile_path)

print("\nLoaded successfully.")
print(f"Number of rows: {len(michigan)}")

print("\nColumns:")
print(michigan.columns.tolist())


# 5. Create 2020 Democratic two-party vote share.
if "PRE20D" in michigan.columns and "PRE20R" in michigan.columns:

    total_two_party_votes = michigan["PRE20D"] + michigan["PRE20R"]

    michigan["dem_share"] = (
        michigan["PRE20D"] / total_two_party_votes
    )

    # 6. Plot the map.
    michigan.plot(
        column="dem_share",
        cmap="RdBu",
        legend=True,
        figsize=(10, 10),
        vmin=0,
        vmax=1,
    )

    plt.title("Michigan 2020 Democratic Two-Party Vote Share")
    plt.axis("off")
    plt.show()

else:
    print(
        "\nThe file loaded, but PRE20D and PRE20R were not found."
    )
    print(
        "Look at the printed column names to identify the correct vote columns."
    )