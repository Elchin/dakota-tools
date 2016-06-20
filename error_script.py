#Function to calculate simulated temperature error in permafrost model
# Jason Cyrus 5/10/16

#import relevant libraries
import numpy as np
from numpy import loadtxt,shape,power,diff
from scipy.integrate import simps,trapz

def error_function():
    #load start temp data
    Tsyn = np.loadtxt('./dump/start0.txt')#reference 'truth'
    Tsim = np.loadtxt('./dump/start.txt')
    #load depth data
    depths = np.loadtxt('./in/grid.txt')

    #Remove first element from arrays
    Tsyn = Tsyn[1:shape(Tsyn)[0]]
    Tsim = Tsim[1:shape(Tsim)[0]]
    depths = depths[1:shape(Tsim)[0]+1]#resize depths to match temps

    #Calculate square error
    err = np.power((Tsim-Tsyn),2)

    #Integrate over depth data using simpsons and trapezoidal method
    Es = simps(err,depths)
    Et = trapz(err,depths)

    #Calculate Error via summation
    Esum = np.vdot(err[0:shape(err)[0]-1],diff(depths))

    #Print results
    print "Simpson's Error: " + str(Es)#:1
    print "Trapezoidal Error: " + str(Et)#:2
    print "Summation Error: " + str(Esum)

    return Es

