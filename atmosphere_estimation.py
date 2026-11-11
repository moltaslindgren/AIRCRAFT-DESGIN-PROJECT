# ----- Model Equations ----- #

from math import *
from matplotlib import pyplot as plt
import numpy as np

T0=288.15
p0=101325
A0=-0.0065

T11 = 216.65
p11 = 22632

T20 = 216.65
p20 = 5475
A20 = 0.001

g0 = 9.80665
R = 287.052
gamma = 1.4
S = 110.4
beta = 1.458e-6

def isa_model_tutorial(h, dt):
    if 0 <= h <= 11000:    # Troposphere
        temperature = T0 + A0*h +dt
        pressure = p0 * (1 + (A0*h/T0))**(-g0/(A0*R))
        density = pressure/(R*temperature)
        mu = beta*temperature**1.5/(temperature+S)
        vu = mu/density
        a = sqrt(gamma*R*temperature)
    elif 11000 < h <= 20000:    # Tropopause
        temperature = T11 + dt
        pressure = p11*exp(-g0*(h-11000)/(R*T11))
        density = pressure / (R * temperature)
        mu = beta * temperature ** 1.5 / (temperature + S)
        vu = mu / density
        a = sqrt(gamma * R * temperature)
    elif 20000 < h <= 32000:    # Stratosphere
        temperature = T20 + A20*(h-20000) + dt
        pressure = p20 * (1 + (A20 * (h-20000) / T20)) ** (-g0 / (A20 * R))
        density = pressure / (R * temperature)
        mu = beta * temperature ** 1.5 / (temperature + S)
        vu = mu / density
        a = sqrt(gamma * R * temperature)
    else:
        print("Error! Invalid altitude!")
        temperature, pressure, density, a, mu, vu = False
        quit()

    return temperature, pressure, density, a, mu, vu


# If running this code directly, the following lines will also be executed:
if __name__ == "__main__":
    h_range = np.linspace(0,32000,1000)

    pressure_list = []
    temperature_list = []
    density_list = []
    speed_of_sound = []
    mu_list = []
    vu_list = []
    for h in h_range:
        temperature_list.append(isa_model_tutorial(h, 0)[0])
        pressure_list.append(isa_model_tutorial(h, 0)[1])
        density_list.append(isa_model_tutorial(h, 0)[2])
        speed_of_sound.append(isa_model_tutorial(h, 0)[3])
        mu_list.append(isa_model_tutorial(h, 0)[4])
        vu_list.append(isa_model_tutorial(h, 0)[5])

    plt.figure()
    plt.plot(temperature_list, h_range)
    plt.ylabel('Altitude [m]')
    plt.xlabel('Temperature [K]')
    plt.ylim([0, 32000])    # Defines limits of y-axis
    plt.xlim([200, 315])    # Defines limits of x-axis
    plt.grid()
    


    plt.figure()
    plt.plot(density_list, h_range)
    plt.ylabel('Altitude [m]')
    plt.xlabel('Density [kg/m³]')
    plt.grid()
   

    plt.figure()
    plt.plot(pressure_list, h_range)
    plt.ylabel('Altitude [m]')
    plt.xlabel('Pressure [Pa]')
    plt.grid()
   

    plt.figure()
    plt.plot(speed_of_sound, h_range)
    plt.ylabel('Altitude [m]')
    plt.xlabel('Speed of sound [m/s]')
    plt.grid()
    plt.show()