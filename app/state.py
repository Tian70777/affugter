from fastapi import FastAPI

# persistent state across the system without circular imports

app = FastAPI()

app.state.shelly_off_timestamp = None