from fastapi import FastAPI

app = FastAPI(
    title="Down Dog API",
    version="1.0.0"
)


@app.get("/")
def root():
    return {"message": "Down Dog API"}
