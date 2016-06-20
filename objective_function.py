#!/usr/bin/env python

#Objective function for error calculation
# -acts as generic python interface to dakota
# Jason Cyrus 5/11/16

# necessary python modules
import sys
import re
import os
import numpy as np
# ----------------------------
# Parse DAKOTA parameters file
# ----------------------------

# setup regular expressions for parameter/label matching
e = '-?(?:\\d+\\.?\\d*|\\.\\d+)[eEdD](?:\\+|-)?\\d+' # exponential notation
f = '-?\\d+\\.\\d*|-?\\.\\d+'                        # floating point
i = '-?\\d+'                                         # integer
value = e+'|'+f+'|'+i                                # numeric field
tag = '\\w+(?::\\w+)*'                               # text tag field

# regular expression for aprepro parameters format
aprepro_regex = re.compile('^\s*\{\s*(' + tag + ')\s*=\s*(' + value +')\s*\}$')
# regular expression for standard parameters format
standard_regex = re.compile('^\s*(' + value +')\s+(' + tag + ')$')

# open DAKOTA parameters file for reading
paramsfile = open(sys.argv[1], 'r')

# extract the parameters from the file and store in a dictionary
paramsdict = {}
for line in paramsfile:
    m = aprepro_regex.match(line)
    if m:
        paramsdict[m.group(1)] = m.group(2)
    else:
        m = standard_regex.match(line)
        if m:
            paramsdict[m.group(2)] = m.group(1)

paramsfile.close()

# crude error checking; handle both standard and aprepro cases
num_vars = 0
if ('variables' in paramsdict):
    num_vars = int(paramsdict['variables'])
elif ('DAKOTA_VARS' in paramsdict):
    num_vars = int(paramsdict['DAKOTA_VARS'])

num_fns = 0
if ('functions' in paramsdict):
    num_fns = int(paramsdict['functions'])
elif ('DAKOTA_FNS' in paramsdict):
    num_fns = int(paramsdict['DAKOTA_FNS'])

#if (num_vars != 2 or num_fns != 1):
#   print "Rosenbrock requires 2 variables and 1 function;\nfound " + \
#        str( num_vars) + " variables and " + str(num_fns) + " functions."
#sys.exit(1)


# -------------------------------
# Convert and send to application
# -------------------------------
# set up the data structures the rosenbrock analysis code expects
# for this simple example, put all the variables into a single hardwired array
continuous_vars = {}

#Dynamically populate continuous_vars list

#Load mineral schema file
data = open('./in/mineral_schema.txt','r')
min_scheme = [line.split() for line in data.readlines()]
min_schema = np.array(min_scheme)
act_vars = min_schema[np.where(min_schema!='*')]

for var in act_vars:
    if (str(var) in paramsdict):
        continuous_vars[str(var)] = float(paramsdict[str(var)])

print continuous_vars
print np.shape(continuous_vars)

active_set_vector = [ int(paramsdict['ASV_1:obj_fn']) ]

# set a dictionary for passing to rosenbrock via Python kwargs
in_params = {}
in_params['cv'] = continuous_vars

in_params['asv'] = active_set_vector
in_params['functions'] = 1


# execute the GIPL error analysis as a separate Python module
from error_optimize import GIPL_runner
out_results = GIPL_runner(**in_params)
print "Completed GIPL."


# ----------------------------
# Return the results to DAKOTA
# ----------------------------

# write the results.out file for return to DAKOTA
# this example only has a single function, so make some assumptions;
# not processing DVV
outfile = open('results.out.tmp', 'w')

# write functions
for func_ind in range(0, num_fns):
    if (active_set_vector[func_ind] & 1):
        functions = out_results['fns']
        outfile.write(str(functions[func_ind]) + ' f' + str(func_ind) + '\n')

# write gradients
for func_ind in range(0, num_fns):
    if (active_set_vector[func_ind] & 2):
        grad = out_results['fnGrads'][func_ind]
        outfile.write('[ ')
        for deriv in grad:
            outfile.write(str(deriv) + ' ')
        outfile.write(']\n')

# write Hessians
for func_ind in range(0, num_fns):
    if (active_set_vector[func_ind] & 4):
        hessian = out_results['fnHessians'][func_ind]
        outfile.write('[[ ')
        for hessrow in hessian:
            for hesscol in hessrow:
                outfile.write(str(hesscol) + ' ')
            outfile.write('\n')
        outfile.write(']]')

outfile.close()

# move the temporary results file to the one DAKOTA expects
import shutil
shutil.move('results.out.tmp', sys.argv[2])
#os.system('mv results.out.tmp ' + sys.argv[2])

