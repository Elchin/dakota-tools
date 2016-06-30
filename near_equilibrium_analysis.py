# Perform local analysis of a point near a response function equillibrium
# Jason Cyrus, June 24 2016
#
# This example will choose a point that is within 7% tolerance of a model's sythetic
# truth and then will explore in a 10% radius about.
#
# In theory we will be able to take our sample data and extrapolate where the
# sythetic truth equillibrium may be.
#
# Practical applications of this is tuning a simulations parameter set that is very
# close to the real world truth values
import dPy
import dakota_report as dr

dakota_samples = {'group':'Dakota_sample_study',
                  'model_id':'GIPL',
                'method':'sampling',
                'scope':'all',
                'seed_pt':{},
                'var_type':'per_expan',
                'per_expan':0.10,
                'scope_type':'uniform_uncertain',
                'samples':300}

dakota_mesh = {'group':'Dakota_coliny_solis_wets',
                'model_id':'GIPL',
                'method':'coliny_solis_wets',
                'scope':'all',
                'seed_pt':{},
                'var_type':'per_expan',
                'per_expan':0.10}

#1D - Parameter Study @ 15 percent radial expansion about seed pt
param_study = { 'group':'equi_param_study',
                'model_id':'GIPL',
                'method':'vector_parameter_study',
                'scope':['a1'],
                'seed_pt':{},
                'var_type':'per_expan',
                'per_expan':0.10,
                'steps':100}

param_study_all = { 'group':'synth_converge_all',
                    'model_id':'GIPL',
                    'method':'vector_parameter_study',
                    'scope':'all',
                'seed_pt':{},
                'var_type':'per_expan',
                'per_expan':0.10,
                'steps':100}

# Grab the GIPL model from the database
model= dr.retrieve_document({'model_id':'GIPL','type':'model'})
# First derive an approximated seed point
offset_seed = dPy.synth_seed(model,0.07)
print offset_seed
# Set seed
param_study['seed_pt'] = offset_seed
#Change param_study tag for organization
param_study['group'] += '_OFFSET'

#Study the parameter space about the offset approximate

#Iterate through parameters performing 1D parameter studies
for param in offset_seed.keys():
    #Change param_study scope
    param_study['scope'][0] = param
    #Perform parameter study
    print 'STARTING PARAM STUDY FOR ' + param
    param_report = dr.execute_dakota(**param_study)
    #Insert report into database
    dr.insert_document(param_report)


# Set seed to synth param set
synth_seed = dPy.get_synth(model)
param_study['seed_pt'] = synth_seed
#Change param_study tag for organization
param_study['group'] += '_SYNTH'

# Now study the parameter space exactly on the synthetic equillibrium
#Iterate through parameters performing 1D parameter studies
for param in offset_seed.keys():
    #Change param_study scope
    param_study['scope'][0] = param
    #Perform parameter study
    print 'STARTING PARAM STUDY FOR ' + param
    param_report = dr.execute_dakota(**param_study)
    #Insert report into database
    dr.insert_document(param_report)

