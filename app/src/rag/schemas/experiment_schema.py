from pydantic import BaseModel

class ExperimentSchema(BaseModel):
    title: str
    description: str
