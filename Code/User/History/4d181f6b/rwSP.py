import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
# Just for dev env
import json

app = FastAPI()

# To Check Alistipes_putredinis LiJ_2017__H3M414933__bin.14

# global vars
ABS_PATH = "./DATA_SG"

# helper function
def fileItr(path: str):
    with open(path) as file:
        yield from file

# Genome ID (tsv's)

# Base Models definations
# class SpeciesList(BaseModel):
#     species: list[str]

@app.post("/getGenomeIDs/")
async def getGenomeFileNames(species_names: list[str]):
    res = {}
    df = pd.read_csv(f"{ABS_PATH}/annotation_files_metadata.csv", header=None)
    grouped_metadata = df.groupby(df.columns[1]).agg(list).to_dict()[0]
    for species_name in species_names:
        genome_names =  grouped_metadata.get(species_name)
        res[species_name] = [ name+".annotations.tsv" for name in genome_names] if genome_names!=None else []
    return res

@app.get("/annotation/{file_name}")
async def get(file_name: str):
    return {"message": file_name}


if __name__ == "__main__":
    df = pd.read_csv(f"{ABS_PATH}/annotation_files_metadata.csv", header=None)
    # for i in range(0):
    # print(df)
    print(json.dumps(df.groupby(df.columns[1]).agg(list).to_dict()[0].get("abs"), indent=4))
