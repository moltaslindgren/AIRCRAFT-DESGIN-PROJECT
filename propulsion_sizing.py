#imports
import numpy as np
import matplotlib.pyplot as plt
import json
#importing results from mass_estimation.py and atmosphere_estimation.py
from atmosphere_estimation import(isa_model_tutorial)

h_cruise = 12192 #40 000 ft in meters
dt = 0 #temperature deviation

temperature, P_ica, density, a, mu, vu = isa_model_tutorial(h_cruise, dt)



#from mass_estimation import(MTOM_LH2, OEM_LH2, fuel_LH2, payload_project, kappa_LH2)
with open("mass_results.json", "r") as file:
    results = json.load(file)

MTOM_LH2 = results["MTOM_LH2"]
OEM_LH2 = results["OEM_LH2"]
fuel_LH2 = results["fuel_LH2"]
payload_project = results["payload_project"]
kappa_LH2 = results["kappa_LH2"]

#propulsion dimensioning
g = 9.80665

#convert the take off mass into take off weight [N]
W_TO = MTOM_LH2 * g

print("\n\n ===========PROPULSION SIZING SCRIPT STARTS HERE============\n")

print(" PROPULSION SIZING INPUTS: ")
print(f"MTOM: {MTOM_LH2:.0f} kg")
print(f"OEM: {OEM_LH2:.0f} kg")
print(f"LH2 mass: {fuel_LH2:.0f} kg")
print(f"Takeoff weight: {W_TO:.0f} N")

#total lift must be equal to Weight to be in equilibrium
Kcr=0.99
C_L=0.5
n_trans= 0.99
n_prop = 0.9
gamma = 1.4
M = 0.75
TR_thr=0.8
epsilon = 1/14 #reciprocal glide ratio 1/(L/D) maybe found from internet? 10-18 from lectures

Wing_Loading = (C_L*1.4*P_ica*M**2)/(2*Kcr) 


v=M*a #take the wanted cruise speed that fits

Power_maximumtakeoffweight_ratio = (Kcr/TR_thr) * ((epsilon*v)/n_trans)

print(f"Wing load ratio (W/S): {Wing_Loading:.0f}")
print(f"Power to maximum take off weight ratio (W/S): {Power_maximumtakeoffweight_ratio:.0f}")

