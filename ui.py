import streamlit as st
import requests

st.title("Airspace Copilot — Demo")

mode = st.sidebar.radio("Mode", ["Traveler", "Ops"])

if mode == "Traveler":
    callsign = st.text_input("Flight callsign or ICAO24")
    question = st.text_input("Ask a question about the flight")
    if st.button("Ask"):
        resp = requests.post("http://localhost:8200/traveler/chat",
                             json={"callsign": callsign, "question": question})
        st.json(resp.json())

else:
    region = st.selectbox("Region", ["Region1"])
    if st.button("Fetch Latest Snapshot"):
        resp = requests.get(f"http://localhost:8100/ops/summary?region={region}")
        st.json(resp.json())
#streamlit run ui.py
