#Python to Dakota generic interface.
#-perform simulation optimization via convient python commands
# Jason Cyrus 5/17/16

import numpy as np
import subprocess
import random as rand

#creates dakota .in file
#must pass in model handle and optimization method one needs performed
def make_dakota(model,**kwargs):
    #evironment section
    enviro = 'environment\n'+'tabular_data\n'+'tabular_data_file = \'dakota_temp.dat\'\n'
    #depending on the method there could be specifics associated with it
    method = 'method \n '+ kwargs['method']+'\n'
    
    #model range
    mod_range = model['range']
    
    ##For Parameter Studies..
    if (kwargs['method'] == 'vector_parameter_study'):
        if (kwargs['var_type']=='per_expan'):
            method += vector_final_pt(kwargs['seed_pt'],kwargs['scope'],kwargs['per_expan'])

        else:
            method+='final_point = ' + str(mod_range[kwargs['scope'][0]][1]) + '\n'

        method+='num_steps = ' + str(kwargs['steps'])
    
    #Add unique identifiers to method
    if 'meth_spec' in kwargs:
        method+=kwargs['meth_spec']
    
    if 'evaluations' in kwargs:
        method+='max_function_evaluations='+str(kwargs['evaluations'])+'\n'

    method+='\n'+ 'model single'
    #Get amount of variables from the scope
    var_amt = np.shape(kwargs['scope'])[0]
    variables = 'variables\n'+'continuous_design = ' + str(var_amt)+'\n'
    interface = ('interface,\n'+ 'fork\n'+ '   analysis_drivers = \'' + model['driver_path'] +'\'\nparameters_file = \'params.in\''+'\nresults_file = \'results.out\'')

    response = 'responses\n'+'objective_functions = 1\n'

    #default is no gradient
    if 'gradient' in kwargs:
        response += kwargs['gradient']
    else:
        response += 'no_gradients\n'

    #hessians not supported in the current version
    response+='no_hessians\n'
    #dynamic part of variables section
    var_dyn = ''
    #manage the variables section...
    if 'var_type' in kwargs:
        if (kwargs['var_type'] == 'per_expan'):#analyze by layer, also means layer number exists'
            if (kwargs['method'] == 'vector_parameter_study'):
                var_dyn = vector_init_pt(kwargs['seed_pt'],kwargs['scope'],kwargs['per_expan'])
            else:
                var_dyn = var_range(kwargs['seed_pt'],kwargs['scope'],kwargs['per_expan'])
        elif (kwargs['var_type'] == 'model_bound'):#ie use the models hard coded var bounds
            if (kwargs['method']=='vector_parameter_study'):
                var_dyn = ('initial_point ' + str(mod_range[kwargs['scope'][0]][0]) +
                           '\ndescriptors \'') + str(kwargs['scope'][0]) + '\'\n'
            else:
                var_dyn = model_range(model,kwargs['scope'])


    #condense into one string
    in_str = enviro + method+'\n'+variables+var_dyn+'\n'+interface+'\n'+response
    #create file
    in_file = open('./dakota_temp.in','w')
    in_file.write(in_str)
    in_file.close()
    #pass back file object
    print 'dakota_temp.in created'
    return in_file



#VARIABLE RANGE GENERATION FUNCTIONS
#

#Will generate the dakota variables for a specific variable scope
def var_range_per(seed,scope,per_expan):
    #percent expansion about point
    range = {}
    lower_bn = []
    upper_bn = []
    start_pt = []
    for s in scope:
        start_pt += [seed[s]]
        lower_bn += [seed[s] - abs(per_expan*seed[s])]
        upper_bn += [seed[s]+ abs(per_expan*seed[s])]

    range['lower'] = lower_bn
    range['upper'] = upper_bn
    return range

def vector_init_pt(seed,scope,per_expan):
    #Grab range
    percent_range = var_range_per(seed,scope,per_expan)['lower']
    var = 'initial_point = '
    for per in percent_range:
        var += str(per)+' '
    var += '\ndescriptors'
    for s in scope:
        var += ' \''+s+'\''
    return var

def vector_final_pt(seed,scope,per_expan):
    #Grab range
    percent_range = var_range_per(seed,scope,per_expan)['upper']
    var = 'final_point = '
    for per in percent_range:
        var += str(per)+' '
    return var
#Will generate the dakota variables for a specific variable scope
def var_range(seed,scope,per_expan):
    #percent expansion about point
    lower_bn = []
    upper_bn = []
    start_pt = []
    for s in scope:
        start_pt += [seed[s]]
        lower_bn += [seed[s] - abs(per_expan*seed[s])]
        upper_bn += [seed[s]+ abs(per_expan*seed[s])]
    print lower_bn
    var = 'initial_point'
    for st in start_pt:
        var += ' '+str(st)
    var += '\nlower_bounds'
    for lw in lower_bn:
        var += ' '+str(lw)
    var += '\nupper_bounds'
    for up in upper_bn:
        var += ' '+str(up)
    var += '\ndescriptors'

    for s in scope:
        var += ' \''+s+'\''

    return var

#Take the range property from a model and generated dakota formatted text
def model_range(m,scope):
    lower_bn = []
    upper_bn = []
    variables = m['range']
    for s in scope:
        lower_bn += [variables[s][0]]
        upper_bn += [variables[s][1]]
    
    var = '\nlower_bounds'
    for lw in lower_bn:
        var += ' '+str(lw)
    var += '\nupper_bounds'
    for up in upper_bn:
        var += ' '+str(up)
    var += '\ndescriptors'
    
    for s in scope:
        var += ' \''+s+'\''
    return var

#Create an initial point range

#Fetch the minimized coefficients from the data file
#will fetch current min value parameter set from current dakota_temp.dat file
def fetch_min_coef():
    # Load Data from Genetic Optimization
    data = open('./dakota_temp.dat','r')
    dataSpl = [line.split() for line in data.readlines()]
    shp = np.shape(dataSpl)
    coef_6 = np.array(dataSpl)[1:-1,2:shp[1]]
    tags = np.array(dataSpl)[0,2:shp[1]]
    #extract minimized coefficiencts
    min_err = coef_6[np.argmin(coef_6[:,shp[1]-3]),:]
    min_param = {}
    i = 0
    for tag in tags:
        min_param[tag] = float(min_err[i])
        i+=1
    return min_param


#will run most recent dakota binding stored in dakota_temp.in
def run_dakota(suppress):
    print 'Running Dakota, please wait...'
    process = subprocess.Popen(['dakota','./dakota_temp.in'],stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            if (suppress):
                print output.strip()
    rc = process.poll()
    print 'Optimization completed.'
    return rc#return formatted stdout

#Update mineral.txt file with array of 24 variables
def update_minerals(params):
    #Edit in mineral file
    minerals = np.loadtxt('./in/mineral.txt',skiprows = 2)
    #load mineral schema
    schema = np.array([line.split() for line in open('./in/mineral_schema.txt').readlines()])
    
    print 'Updating parameters...'
    #Dynamically key match new variables
    for param in params:
        loc = np.where(schema==param)
        print '--------------'
        print param + ':' + str(minerals[loc])
        minerals[loc] = params[param]
        print param + ':' + str(minerals[loc])
    #Cycle through and recreate mineral matrix
    #need to make general
    print 'Parameters Updated.'
    mineralStr = ''
    for i in range(0,6):
        for j in range(0,8):
            mineralStr +=str(minerals[i,j])
            if (j!=7):
                mineralStr+='   '
        if (i!=5):
            mineralStr += '\n'

    #Concatenate on begining
    mineralStr =' 1\n'+'1  6\n' + mineralStr
    #Open and edit file
    mineralTarget = open('./in/mineral.txt','w')
    mineralTarget.truncate();
    mineralTarget.write(mineralStr)
    mineralTarget.close();
    print 'Minerals file updated.'


#read in current minerals file
def retrieve_minerals(params):
    minerals = np.loadtxt('./in/mineral.txt',skiprows = 2)
    #load mineral schema
    schema = np.array([line.split() for line in open('./in/mineral_schema.txt').readlines()])
    min_vals = {}
    for param in params:
        #parameter location in file
        loc = np.where(schema==param)
        print '--------------'
        print param + ':' + str(minerals[loc])
        min_vals[param] = minerals[loc][0]
    
    
    
    return min_vals

#Perform optimization statistics
#Compare current parameter set to synthetic parameter set
def opt_stat(model,params):
    print params
    synth_params = np.loadtxt(model['syn_params'],skiprows = 2)
    schema = np.array([line.split() for line in open(model['schema']).readlines()])
    print 'Parameter % error:'
    errs = {}
    for param in params:
        loc = np.where(schema==str(param))
        print param +':'+ str(params[param])
        if (param in schema):
            err = 100*abs((float(params[str(param)])-synth_params[loc])/synth_params[loc])
            print 'error: '+ str(err[0])
            errs[param] = err[0]

    return errs


#Generate a random seed point from a models boundary ranges
def random_seed(model):
    #grab ranges from model
    ranges = model['range']
    r_seed = {}
    for r in ranges.keys():
        r_seed[r] = rand.uniform(ranges[r][0],ranges[r][1])

    return r_seed

#Will switch keyed params from list a -> to list b
def switch_params(a,b):
    new_b = copy(b)
    for key in a.keys():
        new_b[key] = a[key]
    return new_b


#Will retrieve contents of dakota_temp.dat file
def get_out_data():
    data = open('./dakota_temp.dat','r')
    dataSpl = [line.split() for line in data.readlines()]
    shp = np.shape(dataSpl)
    coef_6 = np.array(dataSpl)[1:-1,2:shp[1]]
    tags = np.array(dataSpl)[0,2:shp[1]]
    out_dat = {}
    cnt = 0
    for t in tags:
        coef_list = coef_6[:,cnt].tolist()
        new_coef = []
        for co in coef_list:
            new_coef += [float(co)]
        #add tag
        out_dat[t] = new_coef
        cnt+=1

    print type(coef_6)
    return out_dat