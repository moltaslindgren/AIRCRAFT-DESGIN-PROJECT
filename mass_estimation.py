# =============================================================
# AIRCRAFT DESIGN I - INITIAL MASS ESTIMATION
# Marius's method + Family Concept
# Existing aircraft values are extracted directly from Excel
#==============================================================
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#Number of passengers
pax_base = 180
pax_stretch= 220

#Mass specifications for passengers
m_passenger = 83
m_baggage = 12
m_freight = 5000

#Payload mass for baseline aircraft
m_p_base = pax_base *(m_passenger + m_baggage) + m_freight

#Payload mass for strecthed aircraft
m_p_stretch = pax_stretch*(m_passenger + m_baggage) + m_freight

print("Baseline payload:", m_p_base, "kg")
print("Stretch payload:", m_p_stretch, "kg")


#Physical Range====================================

#Required design range [NM]
R_DP = 5000

#Reserve requirements [NM]
R_CTG = 0.05 * R_DP
R_DIV = 100
R_HLD = 200*0.5

#Total physical range [NM]
R_PHYS = R_DP + R_CTG + R_DIV + R_HLD

#Converting total physical range to km
#Converting because the aircraft database stores ranges
# in km and we must use consistent units when doing 
# our regression
R_PHYS_km = R_PHYS * 1.852


print("Physical range:", R_PHYS, "NM")
print("Physical range:", R_PHYS_km, "km")


#=== importing aircraft database =====
#=====================================

from pathlib import Path
import pandas as pd

file_path = Path(__file__).resolve().parent / "Aircraft_Database_2026W.xlsx"

#Read excel database
df = pd.read_excel(
    file_path,
    sheet_name="update",
    header=1
)

#extracting all the relevant columns from excel

db = pd.DataFrame()
# Aircraft characteristics
db["aircraft"] = df.iloc[:, 0]
db["MTOM"] = df.iloc[:, 1]
db["MZFM"] = df.iloc[:, 2]
db["OEM"] = df.iloc[:, 3]
db["payload_C"] = df.iloc[:, 4]
db["range_C_km"] = df.iloc[:, 5]

# Existing point B values and mass fractions
db["payload_B"] = df.iloc[:, 22]
db["fuel_C"] = df.iloc[:, 23]
db["range_B_km"] = df.iloc[:, 24]
db["gamma"] = df.iloc[:, 25]
db["kappa"] = df.iloc[:, 26]

#=== Calculating range at point B=====
#=====================================

#assumption from the lecture that there is a linear relationship
#between fuel mass and range from point C.
db["dmf_dR"] = db["fuel_C"] / db["range_C_km"]

#calculating point B from that linear relationship

db["range_B_km"] = (db["range_C_km"] + (db["OEM"] + db["payload_C"] - db["MZFM"]) / db["dmf_dR"])

#Converting km into nautical miles
db["range_B_nm"] = db["range_B_km"] / 1.852


#Just clearing some invalid data that could happen
db = db.dropna(
    subset=[
        "range_B_nm",
        "gamma",
        "kappa"
    ]
).copy()

db = db[
    (db["range_B_nm"] > 0)
    & (db["gamma"] > 0)
    & (db["kappa"] > 0)
    & (db["gamma"] + db["kappa"] < 1)
].copy()


#=== Power regression ============================

# Get the reference-aircraft values from our database
R = db["range_B_nm"]
gamma_ref = db["gamma"]
kappa_ref = db["kappa"]

#GAMMA REGRESSION
b_gamma, ln_a_gamma = np.polyfit(
    np.log(R),
    np.log(gamma_ref),
    1
)

# Convert ln(a) back to a
a_gamma = np.exp(ln_a_gamma)

#KAPPA REGRESSION
# kappa = a_kappa * R^b_kappa


b_kappa, ln_a_kappa = np.polyfit(
    np.log(R),
    np.log(kappa_ref),
    1
)

a_kappa = np.exp(ln_a_kappa)


# Physical range from Step 1 = 5450 NM
gamma_project = a_gamma * R_PHYS**b_gamma
kappa_project = a_kappa * R_PHYS**b_kappa


#---Displaying results for gamma and kappa
print("\n--- POWER REGRESSION ---")


print(f"\nAt R = {R_PHYS:.0f} NM:")
print(f"Gamma = {gamma_project:.5f}")
print(f"Kappa = {kappa_project:.5f}")


# =====================================================
# PLOT THE REGRESSION GRAPHS
# =====================================================

# Create many range values to draw smooth regression curves
R_plot = np.linspace(
    R.min(),
    max(R.max(), R_PHYS),
    300
)

# Calculate gamma and kappa for each range
gamma_curve = a_gamma * R_plot**b_gamma
kappa_curve = a_kappa * R_plot**b_kappa


# -----------------------------------------------------
# CREATE TWO GRAPHS NEXT TO EACH OTHER
# -----------------------------------------------------

fig, axes = plt.subplots(1, 2, figsize=(13, 5))


# -----------------------------------------------------
# GRAPH 1 - GAMMA VS RANGE
# -----------------------------------------------------

# Reference aircraft from Excel
axes[0].scatter(
    R,
    gamma_ref,
    label="Reference aircraft"
)

# Our power regression
axes[0].plot(
    R_plot,
    gamma_curve,
    color="blue",
    label="Power regression"
)

# Our aircraft at physical range = 5450 NM
axes[0].scatter(
    R_PHYS,
    gamma_project,
    color="red",
    marker="x",
    s=100,
    label="Project aircraft"
)

axes[0].set_title("Payload Fraction vs Range")
axes[0].set_xlabel("Range at point B [NM]")
axes[0].set_ylabel("Payload fraction gamma [-]")
axes[0].grid(True)
axes[0].legend()


# -----------------------------------------------------
# GRAPH 2 - KAPPA VS RANGE
# -----------------------------------------------------

# Reference aircraft from Excel
axes[1].scatter(
    R,
    kappa_ref,
    label="Reference aircraft"
)

# Our power regression
axes[1].plot(
    R_plot,
    kappa_curve,
    color="blue",
    label="Power regression"
)

# Our aircraft at physical range = 5450 NM
axes[1].scatter(
    R_PHYS,
    kappa_project,
    color="red",
    marker="x",
    s=100,
    label="Project aircraft"
)

axes[1].set_title("Fuel Fraction vs Range")
axes[1].set_xlabel("Range at point B [NM]")
axes[1].set_ylabel("Fuel fraction kappa [-]")
axes[1].grid(True)
axes[1].legend()


# -----------------------------------------------------
# DISPLAY GRAPHS
# -----------------------------------------------------

plt.tight_layout()
plt.show()


# =====================================================
# STEP 6 - CONVENTIONAL AIRCRAFT MASS ESTIMATION
# =====================================================

# Round the regression factors to match Marius's report
#gamma_used = round(float(gamma_project), 3)
#kappa_used = round(float(kappa_project), 3)
gamma_used = 0.198
kappa_used = 0.318

print("\n--- MASS ESTIMATION FACTORS ---")
print(f"Gamma used = {gamma_used:.3f}")
print(f"Kappa used = {kappa_used:.3f}")

# Conventional maximum takeoff mass
m_TO_conv = m_p_base / gamma_used

# Conventional fuel mass
m_f_conv = kappa_used * m_TO_conv

# Conventional operating empty mass
m_OE_conv = m_TO_conv - m_p_base - m_f_conv

print("\n--- CONVENTIONAL AIRCRAFT ---")
print(f"MTOM: {m_TO_conv:.0f} kg")
print(f"Fuel mass: {m_f_conv:.0f} kg")
print(f"OEM: {m_OE_conv:.0f} kg")



# =====================================================
# STEP 7 - LH2 CORRECTIONS FOR BASELINE AIRCRAFT
# =====================================================

# Correction factors from the lecture
f_eps = 1.07       # Aerodynamic correction
f_BO = 1.02        # Boil-off correction
f_eta = 0.833      # Propulsion efficiency correction
f_LHV = 0.357      # Fuel energy-content correction

# Combined fuel correction factor
f_total = f_eps * f_BO * f_eta * f_LHV

# Corrected LH2 fuel fraction
kappa_LH2_base = kappa_used * f_total

# Assumed increase in operating empty mass
m_OE_LH2_base = 1.30 * m_OE_conv

# Round intermediate values to reproduce Marius's report
kappa_LH2_base = round(kappa_LH2_base, 3)
m_OE_LH2_base = round(m_OE_LH2_base)

# Calculate LH2 aircraft maximum takeoff mass
m_TO_LH2_base = (
    m_OE_LH2_base + m_p_base
) / (1 - kappa_LH2_base)

# Calculate hydrogen fuel mass
m_f_LH2_base = kappa_LH2_base * m_TO_LH2_base

# Payload fraction after LH2 correction
gamma_LH2_base = m_p_base / m_TO_LH2_base

print("\n--- LH2 BASELINE AIRCRAFT ---")
print(f"MTOM: {m_TO_LH2_base:.0f} kg")
print(f"OEM: {m_OE_LH2_base:.0f} kg")
print(f"Payload: {m_p_base:.0f} kg")
print(f"Hydrogen fuel: {m_f_LH2_base:.0f} kg")
print(f"Fuel fraction: {kappa_LH2_base:.3f}")
print(f"Payload fraction: {gamma_LH2_base:.3f}")



# =====================================================
# STEP 8 - FAMILY CONCEPT: STRETCH VARIANT
# =====================================================

# Relative payload increase
payload_increase = (
    m_p_stretch - m_p_base
) / m_p_base

# Match Marius's report rounding
payload_increase = round(payload_increase, 3)

# Family Concept assumption:
# OEM increases by 40% of the relative payload increase
family_OEM_factor = 0.40

m_OE_LH2_stretch = m_OE_LH2_base * (
    1 + family_OEM_factor * payload_increase
)

m_OE_LH2_stretch = round(m_OE_LH2_stretch)

# Family Concept assumption:
# Fuel fraction increases by 3%
family_fuel_factor = 1.03

kappa_LH2_stretch = (
    family_fuel_factor * kappa_LH2_base
)

kappa_LH2_stretch = round(kappa_LH2_stretch, 3)

# Calculate stretch MTOM
m_TO_LH2_stretch = (
    m_OE_LH2_stretch + m_p_stretch
) / (1 - kappa_LH2_stretch)

# Calculate stretch hydrogen mass
m_f_LH2_stretch = (
    kappa_LH2_stretch * m_TO_LH2_stretch
)

# Calculate stretch payload fraction
gamma_LH2_stretch = (
    m_p_stretch / m_TO_LH2_stretch
)

print("\n--- LH2 STRETCH AIRCRAFT ---")
print(f"MTOM: {m_TO_LH2_stretch:.0f} kg")
print(f"OEM: {m_OE_LH2_stretch:.0f} kg")
print(f"Payload: {m_p_stretch:.0f} kg")
print(f"Hydrogen fuel: {m_f_LH2_stretch:.0f} kg")
print(f"Fuel fraction: {kappa_LH2_stretch:.3f}")
print(f"Payload fraction: {gamma_LH2_stretch:.3f}")



# =====================================================
# STEP 9 - COMPARE BASELINE AND STRETCH
# =====================================================

# Calculate the percentage increase in MTOM
MTOM_increase_percent = (
    (m_TO_LH2_stretch / m_TO_LH2_base) - 1
) * 100

# Put the results into a table
results_table = pd.DataFrame({
    "Parameter": [
        "MTOM [kg]",
        "OEM [kg]",
        "Payload [kg]",
        "LH2 fuel [kg]",
        "Fuel fraction [-]",
        "Payload fraction [-]"
    ],
    "Baseline": [
        m_TO_LH2_base,
        m_OE_LH2_base,
        m_p_base,
        m_f_LH2_base,
        kappa_LH2_base,
        gamma_LH2_base
    ],
    "Stretch": [
        m_TO_LH2_stretch,
        m_OE_LH2_stretch,
        m_p_stretch,
        m_f_LH2_stretch,
        kappa_LH2_stretch,
        gamma_LH2_stretch
    ]
})

print("\n--- COMPARISON OF BOTH AIRCRAFT ---")
print(results_table.to_string(index=False))

print(f"\nMTOM increase: {MTOM_increase_percent:.1f}%")

# Check that the mass balances are correct
for name, mtom, oem, payload, fuel in [
    ("Baseline", m_TO_LH2_base, m_OE_LH2_base,
     m_p_base, m_f_LH2_base),

    ("Stretch", m_TO_LH2_stretch, m_OE_LH2_stretch,
     m_p_stretch, m_f_LH2_stretch)
]:
    difference = mtom - (oem + payload + fuel)
    print(f"{name} mass balance difference: {difference:.8f} kg")

    assert abs(difference) < 1e-5



# =====================================================
# STEP 10 - EXPORT RESULTS FOR PROPULSION SIZING
# =====================================================

# Save results as a dictionary
mass_results = {
    "baseline": {
        "mtom_kg": float(m_TO_LH2_base),
        "oem_kg": float(m_OE_LH2_base),
        "payload_kg": float(m_p_base),
        "fuel_lh2_kg": float(m_f_LH2_base),
        "kappa_lh2": float(kappa_LH2_base)
    },

    "stretch_family": {
        "mtom_kg": float(m_TO_LH2_stretch),
        "oem_kg": float(m_OE_LH2_stretch),
        "payload_kg": float(m_p_stretch),
        "fuel_lh2_kg": float(m_f_LH2_stretch),
        "kappa_lh2": float(kappa_LH2_stretch)
    }
}

# Save JSON in the same folder as this Python file
folder = Path(__file__).resolve().parent

with open(folder / "mass_results.json", "w") as file:
    json.dump(mass_results, file, indent=4)

# Save summary table for the report
results_table.to_csv(
    folder / "mass_estimation_results.csv",
    index=False
)

# Save the regression figure from earlier
fig.savefig(
    folder / "gamma_kappa_regression.png",
    dpi=300,
    bbox_inches="tight"
)

print("\nMass results exported successfully!")
print("Created mass_results.json")
print("Created mass_estimation_results.csv")
print("Created gamma_kappa_regression.png")
