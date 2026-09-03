"""
Feasibility spike — locked case study parameters.
Every pull script should import these, not hardcode dates/bboxes separately.
"""

# Dadu district, Sindh — confirmed still partially inundated at year-end
# per Sindh Irrigation Dept projections; one of the hardest-hit districts
# in the 2022 floods (ReliefWeb, PDMA Sindh flood report).
DISTRICT_NAME = "Dadu"
PROVINCE = "Sindh"

# Rough bounding box for Dadu district, Pakistan (WGS84 lon/lat).
# CONFIRM/tighten this against an actual district shapefile before the
# real FYP — this is good enough for a feasibility pull, not for final work.
BBOX = {
    "min_lon": 67.0,
    "max_lon": 68.2,
    "min_lat": 25.9,
    "max_lat": 27.3,
}

# Event window: August was the wettest in Pakistan in 60+ years (Britannica);
# Dadu remained flooded well past the initial peak.
EVENT_START = "2022-08-15"
EVENT_END = "2022-09-15"

# Control window: pre-monsoon 2022, same region, expected non-flood baseline.
CONTROL_START = "2022-05-01"
CONTROL_END = "2022-05-15"
