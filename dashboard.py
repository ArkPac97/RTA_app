import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
import requests

# Odświeżanie co 10 sekund z unikalnym kluczem
count = st_autorefresh(interval=10_000, key="refresh")

st.title("Dashboard anomalii")

@st.cache_data
def load_data(file):
    return pd.read_csv(file)

#ladowanie danychprzy każdym odświeżeniu
def load_fresh_data(file):
    return pd.read_csv(file)

df_margin = load_fresh_data("data/anomalies_margin.csv")
df_discount = load_fresh_data("data/anomalies_discount.csv")

st.write(f"Liczba anomalii marżowych: {len(df_margin)}")
st.write(f"Liczba anomalii rabatowych: {len(df_discount)}")
st.write(f"Łączna liczba anomalii: {len(df_margin) + len(df_discount)}")

fig1, ax1 = plt.subplots()
ax1.hist(df_margin["margin"], bins=20, color="skyblue", edgecolor="black")
ax1.set_title("Rozkład marży w anomaliach marżowych")
ax1.set_xlabel("Marża")
ax1.set_ylabel("Liczba produktów")
st.pyplot(fig1)

fig2, ax2 = plt.subplots()
ax2.hist(df_discount["discount"], bins=20, color="lightgreen", edgecolor="black")
ax2.set_title("Rozkład rabatu w anomaliach rabatowych")
ax2.set_xlabel("Rabat (%)")
ax2.set_ylabel("Liczba produktów")
st.pyplot(fig2)

@st.cache_data(ttl=10)
def fetch_blocked_carts():
    try:
        response = requests.get("http://localhost:5000/carts/blocked")
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        st.error(f"Błąd pobierania zablokowanych koszyków: {e}")
        return []

blocked_carts = fetch_blocked_carts()

st.subheader("Zablokowane koszyki")
st.write(f"Liczba zablokowanych koszyków: {len(blocked_carts)}")

if blocked_carts:
    st.dataframe(blocked_carts)
else:
    st.info("Brak zablokowanych koszyków")
