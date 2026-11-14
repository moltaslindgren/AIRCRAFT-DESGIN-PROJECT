
# =====================================================
# AIRCRAFT DESIGN I - PROPULSION SIZING
# Baseline and Stretch
# Based on Marius's method
# =====================================================

import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path
from atmosphere_estimation import isa_model_tutorial


# =====================================================
# 1. IMPORT MASS ESTIMATION RESULTS
# =====================================================

folder = Path(__file__).resolve().parent

with open(folder / "mass_results.json") as file:
    mass = json.load(file)

m_base = mass["baseline"]["mtom_kg"]
m_stretch = mass["stretch_family"]["mtom_kg"]

# For comparison with Marius's original report:
# m_base = 102931
# m_stretch = 112932

g = 9.80665

W_base = m_base * g
W_stretch = m_stretch * g


# =====================================================
# 2. DESIGN ASSUMPTIONS - MARIUS
# =====================================================

# Flight requirements
M = 0.75
s_TO = 2500.0
s_L = 2500.0
V_APP_max = 140 * 1852 / 3600

#==Altitudes====
h_cruise = 350 * 100 * 0.3048  # FL350 [m] altitude where we cruise (40 000 ft)
h_OEI = 10000 * 0.3048 # altitude we used to check flight with one engine inoperative
h_ceiling = 40000 * 0.3048 #altitude where we check the aircrafts remaining climb capability of 300 ft/min

# Marius uses 100 ft/min.
# use 300 ft/min
# Check against the project requirement of 300 ft/min.
#this is converted to m/min
ROC_ceiling = 300 * 0.3048 / 60

# Motors and propellers
n_motors = 4
n_blades = 6#not used

# Aerodynamics
CL_ref = 0.5
LD_ref = 18.0
AR = 10.0
e0 = 0.85

#efficiency and fuel left
Kcr = 0.99
eta_trans = 0.99
eta_prop_cr = 0.90
TR_cr = 0.80

# Cruise OEI
TR_OEI = 0.95
eta_prop_OEI = 0.90

# Service ceiling
TR_ceiling = 0.90
eta_prop_ceiling = 0.90

# Takeoff OEI
CLmax_TO = 2.0
eps_TO = 1 / 12
eta_ground = 0.70
eta_takeoff_climb = 0.80

#slide 40 defined
friction_ground = 0.03
friction_aero = 0.13

#slide 43 defined
h_obstacle = 35 * 0.3048
TR_TO = 1.0

# Second-segment climb
eta_climb = 0.80
TR_climb = 1.0
eps2_OEI = 0.8*eps_TO

# Landing
#Choosing 
CLmax_L = 2.4
eps_L = 1/6.5
brake = -3.0

h_50 = 50 * 0.3048
landing_factor = 0.70

# Preliminary operational fuel fractions
kappa_ops_base = 0.103
kappa_ops_stretch = 0.106


# =====================================================
# 3. WING LOADING ARRAY
# =====================================================

# Test different takeoff wing loadings [N/m2]
WS = np.linspace(200, 8000, 800)


# =====================================================
# 4. ATMOSPHERIC CONDITIONS
# =====================================================

# Our ISA function returns:
# Temperature, pressure, density, speed of sound, ...

_, p0, rho0, a0, _, _ = isa_model_tutorial(0, 0)

_, pcr, rhocr, acr, _, _ = isa_model_tutorial(h_cruise, 0)

_, poei, rhooei, aoei, _, _ = isa_model_tutorial(h_OEI, 0)

_, pce, rhoce, ace, _, _ = isa_model_tutorial(h_ceiling, 0)

# Cruise speed
vcr = M * acr

# Dynamic pressures
qcr = 0.5 * 1.4 * pcr * M**2
qce = 0.5 * 1.4 * pce * M**2

vce = M * ace


# =====================================================
# 5. DRAG POLAR
# =====================================================

# CD = CD0 + k * CL^2

k = 1 / (np.pi * AR * e0)

# Determine CD0 from reference L/D and CL
CD0 = CL_ref / LD_ref - k * CL_ref**2

if CD0 <= 0:
    raise ValueError("CD0 is negative. Check assumptions.")


# =====================================================
# 6. CRUISE Power Requirement calculation
# =====================================================

# At cruise, W = Kcr * W_TO
CL = Kcr * WS / qcr

# Drag-to-lift ratio
EPS = CD0 / CL + k * CL

# Required installed power-to-weight ratio
PW_cruise = (
    Kcr * EPS * vcr/ (TR_cr * eta_trans * eta_prop_cr))


# =====================================================
# 7. CRUISE OEI - Power to Weight ratio calculation
# =====================================================

# One motor has failed.
# Marius assumes the same dynamic pressure as cruise.

v_OEI = np.sqrt(2 * qcr / rhooei)

# Induced drag is increased by 30%
EPS_OEI = CD0 / CL + 1.3 * k * CL

# Remaining motors must provide required thrust
OEI_factor = n_motors / (n_motors - 1)

PW_OEI = (Kcr * EPS_OEI * v_OEI/ (TR_OEI * eta_trans * eta_prop_OEI)) * OEI_factor


# =====================================================
# 8. SERVICE CEILING - Power to Weight ratio Requirement 
# =====================================================

# At service ceiling, aircraft must still be able to climb 300ft/min.
# Marius uses takeoff weight in this calculation.

CL_ceiling = WS / qce

EPS_ceiling = CD0 / CL_ceiling + k * CL_ceiling

PW_ceiling = (EPS_ceiling * vce + ROC_ceiling) / (TR_ceiling * eta_trans * eta_prop_ceiling)


# =====================================================
# 9. SECOND-SEGMENT CLIMB OEI - Power to weight ratio requirement
# =====================================================

# Climb gradient depends on number of motors
if n_motors == 2:
    climb_gradient = 0.024
elif n_motors == 3:
    climb_gradient = 0.027
else:
    climb_gradient = 0.030

# Speed factor for second segment
F_v2 = 1.08 if n_motors >= 4 else 1.13

# Stall speed at takeoff for every wing loading
v_stall = np.sqrt(2 * WS / (rho0 * CLmax_TO))

v2 = F_v2 * v_stall

# Drag assumption from lecture
EPS_climb = 0.8 * eps_TO

PW_climb = ((climb_gradient + EPS_climb) * v2/ (TR_climb * eta_trans * eta_climb)) * OEI_factor


# =====================================================
# 10. TAKEOFF OEI - Power to Weight ratio requirement
# =====================================================

# Total takeoff distance = s1 + s3
# s1 = ground run
# s3 = initial climb to 35 ft


def takeoff_power(ws):

    # Stall and liftoff speeds
    vs = np.sqrt(2 * ws / (rho0 * CLmax_TO))
    vlof = 1.08 * vs
    v2 = F_v2 * vs

    # Required power for ground run
    def power_ground(s1):

        TW = (1.15 * ws/ (g * rho0 * CLmax_TO * s1* (1 - 1 / (2 * n_motors))* (1 - friction_ground - friction_aero)))

        return (TW * (0.71 * vlof)/ (TR_TO * eta_trans * eta_ground))

    # Required power for initial climb
    def power_air(s3):

        TW = (np.sin(np.arctan(h_obstacle / s3))+ eps_TO) / (1 - 1 / n_motors)

        return (TW * (vlof + v2) / 2/ (TR_TO * eta_trans * eta_takeoff_climb))

    # Find s1 and s3 where their required powers match
    low = 0.001
    high = s_TO - 0.001

    for i in range(50):

        s1 = (low + high) / 2
        s3 = s_TO - s1

        if power_ground(s1) > power_air(s3):
            low = s1
        else:
            high = s1

    return power_ground((low + high) / 2)


# Repeat takeoff calculation for every wing loading
PW_takeoff = np.array([takeoff_power(ws) for ws in WS])


# =====================================================
# 11. APPROACH SPEED AND LANDING DISTANCE
# =====================================================

# Maximum landing wing loading from approach speed
WS_L_approach = (0.5 * rho0 * CLmax_L* (V_APP_max / 1.23)**2)

# Landing speed factor
F_vL = 1.08 if n_motors >= 4 else 1.13

# Landing distance coefficient from lecture
B = ((1.23**2 - F_vL**2) / (g * eps_L)- F_vL**2 / brake) / (rho0 * CLmax_L)

# Maximum landing wing loading from landing distance
WS_L_landing = (landing_factor * s_L - h_50 / eps_L) / B

# Convert landing W/S limits to takeoff W/S limits

# Baseline
WS_app_base = WS_L_approach / (1 - kappa_ops_base)
WS_land_base = WS_L_landing / (1 - kappa_ops_base)

# Stretch
WS_app_stretch = WS_L_approach / (1 - kappa_ops_stretch)
WS_land_stretch = WS_L_landing / (1 - kappa_ops_stretch)


# =====================================================
# 12. FIND REQUIRED P/W AND CHOOSE DESIGN POINT
# =====================================================

# Collect all five power requirements
PW_all = np.vstack([PW_cruise, PW_OEI, PW_ceiling, PW_climb, PW_takeoff])

# Highest P/W at each wing loading
PW_required = PW_all.max(axis=0)

# Stretch must share the baseline wing
mass_ratio = m_stretch / m_base

# Maximum baseline W/S allowed by both aircraft
WS_limit_base = min(WS_app_base, WS_land_base, WS_app_stretch / mass_ratio,WS_land_stretch / mass_ratio)

# Only consider allowed wing loadings
valid = WS <= WS_limit_base

if not np.any(valid):
    raise ValueError("No feasible wing loading in the grid.")

# Choose W/S with the lowest required P/W
WS_base = WS[valid][np.argmin(PW_required[valid])]

PW_base = float(np.interp( WS_base, WS, PW_required))

# Calculate wing area
S = W_base / WS_base

# Stretch has the same wing area
WS_stretch = W_stretch / S

if WS_stretch > WS.max():
    raise ValueError("Increase the maximum WS grid value.")

PW_stretch = float(np.interp(
    WS_stretch, WS, PW_required
))


# =====================================================
# 13. INSTALLED POWER AND PROPELLER SIZE
# =====================================================

# Propeller diameter factor for 6 blades
K_prop = 0.49

for name, weight, ws, pw in [("Baseline", W_base, WS_base, PW_base),("Stretch", W_stretch, WS_stretch, PW_stretch)]:

    # Total installed motor power
    P0 = pw * weight

    # Shaft power after transmission losses
    Pshaft = P0 * eta_trans

    # Propeller diameter from lecture correlation
    D = K_prop * (Pshaft / n_motors / 1000)**0.25

    print(f"\n{name}")
    print(f"  W/S: {ws:.0f} N/m2")
    print(f"  P/W: {pw:.2f} W/N")
    print(f"  Wing area: {S:.1f} m2")
    print(f"  Installed power: {P0/1e6:.2f} MW")
    print(f"  Shaft power per propeller: {Pshaft/n_motors/1e6:.2f} MW")
    print(f"  Propeller diameter: {D:.2f} m")


# =====================================================
# 14. PLOT P/W VS W/S
# =====================================================

plt.figure(figsize=(10, 7))

plt.plot(WS, PW_cruise, label="Cruise")
plt.plot(WS, PW_OEI, label="Cruise OEI")
plt.plot(WS, PW_takeoff, label="Takeoff OEI")
plt.plot(WS, PW_climb, label="Climb OEI")
plt.plot(WS, PW_ceiling, label="Service ceiling")

# Highest requirement at each wing loading
plt.plot(WS, PW_required, "k--", label="Required P/W")

# Vertical wing loading limits
plt.axvline(
    WS_land_base,
    color="tab:red",
    linestyle=":",
    label="Landing limit - baseline"
)

plt.axvline(
    WS_app_base,
    color="tab:purple",
    linestyle=":",
    label="Approach limit - baseline"
)

plt.axvline(
    WS_limit_base,
    color="black",
    linestyle="-.",
    label="Family wing limit"
)

# Baseline and stretch design points
plt.scatter(
    [WS_base, WS_stretch],
    [PW_base, PW_stretch],
    color=["blue", "red"],
    zorder=5
)

plt.xlabel("Takeoff wing loading W/S [N/m2]")
plt.ylabel("Installed power-to-weight ratio P0/W_TO [W/N]")
plt.title("Propulsion sizing - baseline and stretch")

plt.ylim(0, 40)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

print("Approach limit:", WS_app_base)
print("Landing limit:", WS_land_base)
print("Family wing limit:", WS_limit_base)

labels = ["Cruise", "Cruise OEI", "Ceiling",
          "Climb OEI", "Takeoff OEI"]

i = np.argmin(abs(WS - WS_base))
print("Active power constraint:",
      labels[np.argmax(PW_all[:, i])])