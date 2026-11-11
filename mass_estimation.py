#-------------------
#ACD1 - MASS ESTIMATION SCRIPT
#---------------------
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt


#---------------------------------
#Reading excel aircraft database
#---------------------------------

file = "Aircraft_Database_2026W.xlsx"
df = pd.read_excel(file, sheet_name="update", header=None)
data = pd.DataFrame()

#Storing
data["Aircraft"] = df.iloc[:, 0]
data["MTOM"] = pd.to_numeric(df.iloc[:, 1], errors="coerce")
data["MZFM"] = pd.to_numeric(df.iloc[:, 2], errors="coerce")
data["OEM"] = pd.to_numeric(df.iloc[:, 3], errors="coerce")
data["payload_C"] = pd.to_numeric(df.iloc[:, 4], errors="coerce")
data["range_C_km"] = pd.to_numeric(df.iloc[:, 5], errors="coerce")


#Removing aircraft with missing information
data = data.dropna().copy()

#--------------------------------------------------------------------------
#Step 2 - Calculating point B (range at maximum payload) in the 
# payload range diagram based on the given point C (payload at maximumfuel)
#----------------------------------------------------------------------------


#MZFM= OEM + maximum payload
data["payload_B"] = data["MZFM"] - data["OEM"] 

#at point B:
#MTOM = MZFM + fuel_B
data["fuel_B"] = data["MTOM"] - data["MZFM"]


#At point C: MTOM = OEM + payload_C + fuel_C
data["fuel_C"] = (data["MTOM"] - data["OEM"] - data["payload_C"])


#got this from initial mass est pdf slide 14
#-----------------------------------------------------
#fuel mass per km [kg/km]
data["dmf_dR"] = data["fuel_C"] / data["range_C_km"]

#calculating range at maximum payload point (point B)
data["range_B_km"] = (data["range_C_km"] + (data["OEM"] + data["payload_C"] - data["MZFM"])/data["dmf_dR"])


#only displaying the first 10 for safety check
#print("\nRANGE AT POINT B:")
#print(data[["Aircraft", "range_C_km", "range_B_km"]].head(10))
#print("\n")



#---------------------------------------------
# STEP 3: calculating payload and fuel fractions
#-----------------------------------------------

# gamma = maximum payload/ maximum takeoff mass
data["gamma"] = data["payload_B"] / data["MTOM"]

# kappa = fuel mass at point B / maximum takeoff mass
data["kappa"] = data["fuel_B"] / data["MTOM"]

#only displaying the first 10 for safety check
#print("\npayload and fuel fractions:")
#print(data[["Aircraft", "range_B_km", "gamma", "kappa"]].head(10))
#print("\n")

#only displaying the first 10 for safety check
data["OEM_fraction"] = data["OEM"] / data["MTOM"]
#print(data[["gamma", "kappa", "OEM_fraction"]].head())
#print("\n")


#-----------------------------------------
# plotting gamma and kappa against range
#-----------------------------------------

R = data["range_B_km"]

gamma = data["gamma"]
kappa = data["kappa"]

# Remove invalid rows before regression
valid = (
    np.isfinite(R)
    & np.isfinite(gamma)
    & np.isfinite(kappa)
    & (R > 0)
    & (gamma > 0)
    & (kappa > 0)
    & (gamma + kappa < 1)
)

R = R[valid]
gamma = gamma[valid]
kappa = kappa[valid]


#print("Number of aircraft used:", len(R))

# Plot gamma against range
plt.figure(figsize=(9, 5))
plt.scatter(R, gamma)
plt.xlabel("Range at point B [km]")
plt.ylabel("Payload fraction gamma [-]")
plt.title("Payload fraction vs range")
plt.grid(True)

# Plot kappa against range
plt.figure(figsize=(9, 5))
plt.scatter(R, kappa)
plt.xlabel("Range at point B [km]")
plt.ylabel("Fuel fraction kappa [-]")
plt.title("Fuel fraction vs range")
plt.grid(True)

plt.show()


#CHATGPT PLOTTING SCRIPT from here
#-----------------------------------------
# PROJECT AIRCRAFT PHYSICAL RANGE
#-----------------------------------------

R_design_nm = 5000
R_contingency_nm = 0.05 * R_design_nm
R_alternate_nm = 100
R_holding_nm = 200 * 0.5

R_physical_nm = (R_design_nm + R_contingency_nm + R_alternate_nm + R_holding_nm)

R_project = R_physical_nm * 1.852

print(f"Project physical range: {R_project:.1f} km")


#-----------------------------------------
# LINEAR REGRESSION
#-----------------------------------------

# Fit straight lines: y = a*x + b
gamma_coeff = np.polyfit(R, gamma, 1)
kappa_coeff = np.polyfit(R, kappa, 1)

# Estimate gamma and kappa at our project range
gamma_project = np.polyval(gamma_coeff, R_project)
kappa_project = np.polyval(kappa_coeff, R_project)

print("\nREGRESSION RESULTS:")
print(f"Gamma = {gamma_project:.4f}")
print(f"Kappa = {kappa_project:.4f}")

# Check whether the project range is covered by the database
if R_project < R.min() or R_project > R.max():
    print("WARNING: Project range is outside the database range!")


#-----------------------------------------
# CREATE REGRESSION LINES
#-----------------------------------------

R_line = np.linspace(
    min(R.min(), R_project),
    max(R.max(), R_project),
    300
)

gamma_line = np.polyval(gamma_coeff, R_line)
kappa_line = np.polyval(kappa_coeff, R_line)


# ---------------------------------------------------------
# POWER REGRESSION: y = a * R^b
# ---------------------------------------------------------

# We use logarithms:
# ln(y) = ln(a) + b * ln(R)

# Fit gamma
b_gamma, ln_a_gamma = np.polyfit(
    np.log(R), np.log(gamma), 1
)
a_gamma = np.exp(ln_a_gamma)

# Fit kappa
b_kappa, ln_a_kappa = np.polyfit(
    np.log(R), np.log(kappa), 1
)
a_kappa = np.exp(ln_a_kappa)

print("\nPOWER REGRESSION EQUATIONS:")
print(f"Gamma = {a_gamma:.6f} * R^({b_gamma:.4f})")
print(f"Kappa = {a_kappa:.6f} * R^({b_kappa:.4f})")

# Project range [km]
R_project = 5450 * 1.852

# Calculate project values
gamma_project = a_gamma * R_project**b_gamma
kappa_project = a_kappa * R_project**b_kappa

print("\nPROJECT ESTIMATES:")
print(f"Gamma = {gamma_project:.4f}")
print(f"Kappa = {kappa_project:.4f}")

# Draw smooth regression curves
R_line = np.linspace(
    R.min(),
    max(R.max(), R_project),
    300
)

gamma_line = a_gamma * R_line**b_gamma
kappa_line = a_kappa * R_line**b_kappa

# Gamma graph
plt.figure(figsize=(9, 5))
plt.scatter(R, gamma, alpha=0.5, label="Aircraft database")
plt.plot(R_line, gamma_line, color="blue",
         label="Power regression")
plt.scatter(R_project, gamma_project, color="red",
            marker="x", s=120, label="Our aircraft")
plt.axvline(R_project, color="red", linestyle="--", alpha=0.5)
plt.axhline(gamma_project, color="red", linestyle="--", alpha=0.5)
plt.xlabel("Range at point B [km]")
plt.ylabel("Gamma [-]")
plt.title("Gamma vs Range - Power Regression")
plt.legend()
plt.grid(True)

# Kappa graph
plt.figure(figsize=(9, 5))
plt.scatter(R, kappa, alpha=0.5, label="Aircraft database")
plt.plot(R_line, kappa_line, color="blue",
         label="Power regression")
plt.scatter(R_project, kappa_project, color="red",
            marker="x", s=120, label="Our aircraft")
plt.axvline(R_project, color="red", linestyle="--", alpha=0.5)
plt.axhline(kappa_project, color="red", linestyle="--", alpha=0.5)
plt.xlabel("Range at point B [km]")
plt.ylabel("Kappa [-]")
plt.title("Kappa vs Range - Power Regression")
plt.legend()
plt.grid(True)

plt.show()




#-----------------------------
#INITIAL MASS ESTIMATION
#-----------------------------

#payload from design specifications
passengers = 180
passengers_max = 220
passenger_mass = 83
baggage_mass = 12
freight_mass = 5000

# Total payload
payload_project = (passengers*(passenger_mass + baggage_mass) + freight_mass)
payload_max_project = (passengers_max*(passenger_mass + baggage_mass) + freight_mass)

# checking that gamma and kappa are physically possible
if gamma_project <= 0:
    raise ValueError("Gamma must be positive.")

if kappa_project <= 0:
    raise ValueError("Kappa must be positive.")

if gamma_project + kappa_project >= 1:
    raise ValueError("Gamma + kappa must be smaller than 1.")

#Maximum takeoff mass
MTOM_project = payload_project / gamma_project
MTOM_project_max = payload_max_project / gamma_project

# Fuel mass
fuel_project = kappa_project * MTOM_project
fuel_project_max = kappa_project * MTOM_project_max


# Operating empty mass
OEM_project = MTOM_project - payload_project - fuel_project
OEM_project_max = MTOM_project_max - payload_max_project - fuel_project_max


print("\n--------------------------------")
print("CONVENTIONAL AIRCRAFT ESTIMATE")
print("--------------------------------")

print(f"Payload: {payload_project:.0f} kg")
print(f"MTOM: {MTOM_project:.0f} kg")
print(f"Fuel mass: {fuel_project:.0f} kg")
print(f"OEM: {OEM_project:.0f} kg")

print("\n Max passengers payload aircraft estimate")
print(f"Payload: {payload_max_project:.0f} kg")
print(f"MTOM: {MTOM_project_max:.0f} kg")
print(f"Fuel mass: {fuel_project_max:.0f} kg")
print(f"OEM: {OEM_project_max:.0f} kg")



#CHAT GPT SCRIPT FROM HERE----
#-----------------------------------------------------
# STEP 7 - LH2 FUEL-CELL ELECTRIC CORRECTIONS
#-----------------------------------------------------

# Correction factors from Initial Mass Estimation lecture
f_drag = 1.07
f_boiloff = 1.02
f_efficiency = 0.833
f_LHV = 0.357

# Total correction factor
f_total = (
    f_drag
    * f_boiloff
    * f_efficiency
    * f_LHV
)

# Corrected fuel fraction
kappa_LH2 = kappa_project * f_total

# Course assumption: 30% higher operating empty mass
OEM_LH2 = 1.30 * OEM_project

# New maximum takeoff mass
MTOM_LH2 = (
    OEM_LH2 + payload_project
) / (1 - kappa_LH2)

MTOM_LH2_max = (
    OEM_LH2 + payload_max_project
) / (1 - kappa_LH2)


# Hydrogen fuel mass
fuel_LH2 = kappa_LH2 * MTOM_LH2
fuel_LH2_max = kappa_LH2 * MTOM_LH2_max

print("\n--------------------------------")
print("LH2 FUEL-CELL ELECTRIC AIRCRAFT")
print("--------------------------------")

print(f"Corrected kappa: {kappa_LH2:.4f}")
print(f"Payload: {payload_project:.0f} kg")
print(f"OEM: {OEM_LH2:.0f} kg")
print(f"MTOM: {MTOM_LH2:.0f} kg")
print(f"MTOM max passengers: {MTOM_LH2_max:.0f} kg")
print("\n")
print(f"LH2 fuel mass: {fuel_LH2:.0f} kg")
print(f"LH2 fuel mass (max passengers): {fuel_LH2_max:.0f} kg")


# Check mass balance
mass_check = OEM_LH2 + payload_project + fuel_LH2
print("\n")
print(f"Mass balance check: {mass_check:.0f} kg")
#CHATGPT SCRIPT TO HERE


results = {
    "MTOM_LH2": float(MTOM_LH2),
    "OEM_LH2": float(OEM_LH2),
    "fuel_LH2": float(fuel_LH2),
    "payload_project": float(payload_project),
    "kappa_LH2": float(kappa_LH2)
}

with open("mass_results.json", "w") as file:
    json.dump(results, file, indent=4)

print("Mass estimation results saved!")