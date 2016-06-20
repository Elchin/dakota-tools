#Blackbox GIPL sim to optimize conductivity coefficients
# Jason Cyrus 5/11/16

import os
import numpy as np
from numpy import loadtxt,shape

def GIPL_runner(**kwargs):
    
    #Grab variables from input
    parameters = kwargs['cv']
    ASV = kwargs['asv']
    
    #Edit in mineral file
    minerals = np.loadtxt('./in/mineral.txt',skiprows = 2)
    #Load mineral schema file
    data = open('./in/mineral_schema.txt','r')
    min_scheme = [line.split() for line in data.readlines()]
    print 'Current mineral data:\n' + str(minerals)
    print 'Changing paramereters...'
    #Dynamically change  coefficients,
    for param in parameters:
        loc = np.where(np.array(min_scheme)==str(param))
        minerals[loc] = parameters[param]#key match value
    
    #Cycle through and recreate mineral matrix
    mineralStr = ''
    for i in range(0,6):
        for j in range(0,8):
            mineralStr +=str(minerals[i,j])
            if (j!=7):
                mineralStr+='   '

        if (i!=5):
            mineralStr += '\n'

    print 'New mineral data:\n' + str(minerals)
    #Concatenate on begining
    mineralStr =' 1\n'+'1  6\n' + mineralStr
    #Open and edit file
    mineralTarget = open('./in/mineral.txt','w')
    mineralTarget.truncate();
    mineralTarget.write(mineralStr)
    mineralTarget.close();
    
    #Rerun GIPL simulation
    print "Running GIPL..."
    #Try running the fortran script from here...
    os.system('./gipl')
    print "GIPL completed."

    #Files have been updated so rerun error calculation
    from error_script import error_function
    obj_err = error_function()

    #Wrap data nicely for Dakota
    retval = dict([])
    if (ASV[0] & 1): # **** f: Function
        retval['fns'] = [obj_err]

    return(retval)