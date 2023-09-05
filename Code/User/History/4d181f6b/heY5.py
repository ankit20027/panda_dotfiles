import io
import zipfile
from os import path
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
# Just for dev env
# uvicorn api:app --reload
import json

app = FastAPI()

# global vars
ABS_PATH = "./DATA_SG"

# helper function
def fileItr(path: str):
    with open(path, mode='rb') as file:
        yield from file


####################
# Genome ID (tsv's)#
####################
@app.post("/getGenomeIDs/")
async def getGenomeFileNames(species_names: list[str]):

    # Get genome id file names for given species
    res = {}
    df = pd.read_csv(f"{ABS_PATH}/annotation_files_metadata.csv", header=None)
    grouped_metadata = df.groupby(df.columns[1]).agg(list).to_dict()[df.columns[0]]

    # Create response body
    for species_name in species_names:
        genome_names =  grouped_metadata.get(species_name)
        res[species_name] = genome_names if genome_names!=None else []
    return res


@app.post("/annotationZip/")
async def getTsvZip(file_names: list[str]):

    # Create new metadat from user input
    metadata_csv = pd.read_csv(f"{ABS_PATH}/annotation_files_metadata.csv", header=None)
    metadata_csv = metadata_csv.rename({metadata_csv.columns[0]: "genome_ID"}, axis=1)
    new_metadata = pd.merge(pd.DataFrame({"genome_ID": file_names}), metadata_csv, on=["genome_ID"])
    metadata_dict = new_metadata.groupby(new_metadata.columns[1]).agg(list).to_dict()[metadata_csv.columns[0]]

    # Save from the aquired metadata
    buffer = io.BytesIO()
    zf = zipfile.ZipFile(buffer, mode='w')
    for species, genome_id_list in metadata_dict.items():
        for genome_id in genome_id_list:
            genome_file_path = f"{ABS_PATH}/annotation_files/{genome_id}.annotations.tsv"
            if (path.exists(genome_file_path)):
                zf.write(f"{ABS_PATH}/annotation_files/{genome_id}.annotations.tsv", f"{species}/{genome_id}.annotations.tsv")
    zf.close()

    # Send the zip back to user
    return StreamingResponse(
        iter([buffer.getvalue()]), 
        media_type="application/x-zip-compressed",
        headers = {"Content-Disposition":"attachment;filename=annotations.zip",
                   "Content-Length": str(buffer.getbuffer().nbytes)})


####################
# Features  (csv's)#
####################
@app.post("/featuresFile/")
async def getFeatureFile(species_names: list[str], func_type: str):

    # get species list in lowercase eg. "cazy"
    func_df = pd.read_csv(f"{ABS_PATH}/species_functionality_matrix_{func_type}.csv")
    req_df = func_df.loc[func_df[func_df.columns[0]].isin(species_names)]
    req_df =  req_df.T if len(species_names) == 1 else req_df

    # Send csv as response
    buffer = io.BytesIO()
    req_df.to_csv(buffer, index=False)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment;filename=FunctionalProfile.csv",
                 "Content-Length": str(buffer.getbuffer().nbytes)}
    )



if __name__ == "__main__":
    # Anaerotruncus_colihominis single Clostridium_butyricum double
    species_names = ["Anaerotruncus_colihominis", "Clostridium_butyricum"]
    func_type = "cazy"
    func_df = pd.read_csv(f"{ABS_PATH}/species_functionality_matrix_{func_type}.csv", index_col=None)
    req_df = func_df.loc[func_df[func_df.columns[0]].isin(species_names)]
    req_df =  req_df.T if len(species_names) == 1 else req_df
    print(req_df)
    # buffer = io.BytesIO()
    # req_df.to_csv(buffer, index=False)
    # return StreamingResponse(
    #     iter([buffer.getvalue()]),
    #     media_type="text/csv",
    #     headers={"Content-Disposition": "attachment;filename=FunctionalProfile.csv",
    #              "Content-Length": str(buffer.getbuffer().nbytes)}
    # )