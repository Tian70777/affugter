from fastapi import FastAPI

# persistent state across the system without circular imports

app = FastAPI()

app.state.shelly_off_timestamp = None

# add state for threshold, so it can be accessed from anywhere without circular imports
app.state.threshold = None
app.state.threshold_date = None

