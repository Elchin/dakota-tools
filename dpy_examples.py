#Examples of using Dakota with Python and writing reports to a local MongoDB database for further analysis

import dakota_report as dr

###Dakota is treated as a 3rd party service that is interacted with via the dakota_report library allowing dakota operations such as optimization and parameter studies and then storing the output from them.

###This example will use a genetic optimization algorithm to find an approximate global min and
#  equillibrium in the objective function. It will then begin a 1D parameter study on each coefficient
#  about the point to investigate equillibrium behavior.

###Our two input report modules. Note they are linked with the 'group' tag

#Genetic Optimization
gene_report = { 'group':'Genetic_param_study01',
                'model_id':'GIPL',
                'method':'genie_direct',
                'var_type':'model_bound',
                'scope':'all',
                'evaluations':3000}

#1D - Parameter Study @ 15 percent radial expansion about seed pt
param_study = { 'group':'Genetic_param_study02',
                'model_id':'GIPL',
                'method':'vector_parameter_study',
                'scope':['a1'],
                'seed_pt':{},
                'var_type':'per_expan',
                'per_expan':0.10,
                'steps':100}




#call 'execute_dakota' with a genetic optimiaz
#gene_report = dr.execute_dakota(**gene_report)
#insert genetic report into database
#dr.insert_document(gene_report)

#OR... Retrieve the report from the database
gene_report = dr.retrieve_document({'group':'Genetic_param_study','method':'genie_direct'})


#Retrieve the optimized post parameters from the report
gene_params = gene_report['post_params']
#remove obj_fun parameter
gene_params.pop('obj_fn',None)
#Set the param studys' seed
param_study['seed_pt'] = gene_params

#Iterate through parameters performing 1D parameter studies
for param in gene_params.keys():
    #Change param_study scope
    param_study['scope'][0] = param
    #Perform parameter study
    print 'STARTING PARAM STUDY FOR ' + param
    param_report = dr.execute_dakota(**param_study)
    #Insert report into database
    dr.insert_document(param_report)


