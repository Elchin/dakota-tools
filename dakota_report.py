#Dakota Report generation module
# Jason Cyrus 5/26/16
# Will go through the entire process of optimization and record it into a document
#
# Steps: 1) Load initial info
#        2) Generate .in file
#        3) Initiate Dakota
#        4) Perform post analysis
#        5) Generate Document report

import numpy as np
from datetime import datetime
import dPy
import pymongo
from pymongo import MongoClient
import error_script as er
import copy
from bson.objectid import ObjectId

#Model Staging Ground - what report generation will expect.

#syntax of a 'model'
GIPL = {'type':'model',
        'model_id':'GIPL',
        'driver_path':'objective_function.py',
        'params':'./in/mineral.txt',
        'syn_params':'./in/mineral_copy.txt',
        'schema':'./in/mineral_schema.txt',
        'sim_out':'./dump/start.txt',
        'syn_out':'./dump/start0.txt',
        'range':{'a1':[0.05,0.09],'a2':[0,0.002],'a3':[0.04,0.08],'a4':[0.04,0.08],
            'a5':[0.01,0.035],'a6':[0.05,0.085],'b1':[-0.33,-0.1],'b2':[-1.1,-0.7],
            'b3':[-0.8,-0.4],'b4':[-1.5,-0.5],'b5':[-0.25,0],'b6':[-0.35,-0.1],
            'kt1':[1.02,1.07],'kt2':[0.6,1.0],'kt3':[1.0,1.4],'kt4':[1.2,1.6],
            'kt5':[1.6,1.9],'kt6':[2.2,2.6],'kf1':[2.0,2.1],'kf2':[2.0,2.1],
            'kf3':[2.05,2.25],'kf4':[2.45,2.7],'kf5':[2.0,2.1],'kf6':[2.4,2.8]}
        }

#
#syntax of an 'action'
optimization_report = {
'model_id':'GIPL',
'method':'genie_direct',
#use a point generated from genetic search
'seed_pt':{'a1':7.48600104e-02,'b1':-1.37928040e-01,'kt1':1.03162227e+00,'kf1':2.16544961e+00,
         'a2':5.90098068e-04,'b2':-8.58437304e-01,'kt2':7.89647715e-01,'kf2':2.11899512e+00,
         'a3':4.70507772e-02,'b3':-7.44334447e-01,'kt3':1.21235057e+00 ,'kf3':2.06905450e+00,
         'a4':7.16175659e-02,'b4':-2.58090623e-01,'kt4':1.34361894e+00,'kf4':2.63343283e+00,
         'a5':1.92814890e-02,'b5':-1.16556259e-01,'kf5':1.59823878e+00,'kf5':2.05464736e+00,
        'a6':5.76307924e-02,'b6':-1.83317563e-01,'kt6':2.27752833e+00,'kf6':2.75607339e+00},
        #percent expansion about seed point
        'var_type':'per_expan',
        'per_expan':0.1,
        'scope':['a1','a2','a3','a4','a5','a6']
}
###

#Report generation module
def execute_dakota(**kwargs):
    print 'Starting Dakota Report Generation...'
    dakota_pkg = {}
    dakota_pkg = copy.deepcopy(kwargs)
    
    #Get date and time
    date = datetime.utcnow()
    print 'Date & Time: ' + str(date)
    dakota_pkg['date_time'] = date
    print '----------------------------------------'
    
    #load model based off it's model_id
    model=retrieve_document({'model_id':kwargs['model_id'],'type':'model'})

    seed = {}
    #First set mineral parameters to current point
    if ('seed_pt' in kwargs):
        my_seed = kwargs['seed_pt']
        dPy.update_minerals(my_seed)
        dakota_pkg['seed_pt'] = my_seed
        seed = my_seed
    else:
        #Or use a random point in the models range
        rand_seed = dPy.random_seed(model)
        dPy.update_minerals(rand_seed)
        dakota_pkg['seed_pt'] = rand_seed
        seed = rand_seed

    #Check to see if variable range is all
    if (kwargs['scope'] == 'all'):
        #change scope to everything
        kwargs['scope'] = seed.keys()

    #Get initial objective function
    obj_fun_pre = er.error_function()
    #add obj fun to package
    dakota_pkg['obj_fun_pre'] = obj_fun_pre
    #Retrieve pre-processed parameters
    print 'Current parameter set:\n' + str(dPy.retrieve_minerals(kwargs['scope']))
    
    #Add current params to package
    cur_param = dPy.retrieve_minerals(kwargs['scope'])
    dakota_pkg['pre_params'] = cur_param
    
    #Perform initial parameter error check
    cur_err = dPy.opt_stat(model,cur_param)
    print 'Current Error: ' + str(cur_err)
    #Add initial error to package
    dakota_pkg['pre_error'] = cur_err
    
    
    #Based on current input will generate appropriate dakota.in file
    dPy.make_dakota(model,**kwargs)
    
    #Run Dakota Optimization...
    #dakota_temp.in should have been created, now execute it w/ live output
    #runs most recent make_dakota config
    dPy.run_dakota(1)

    #Retrieve optimized paramter set
    #dakota_temp.dat now contains data from optimization sequence
    #pull out minimized coefficients
    print 'Minimized Coefficents:'
    min_param =dPy.fetch_min_coef()
    #Add final params to package
    dakota_pkg['post_params'] = min_param
    #add optimized coefficients back into model
    dPy.update_minerals(min_param)
    print min_param
    #add obj fun to package
    dakota_pkg['obj_fun_post'] = min_param['obj_fn']
    
    #add contents of output data file into package
    dakota_pkg['out_data'] = dPy.get_out_data()
    #Perform post param error analysis
    new_err = dPy.opt_stat(model,min_param)
    dakota_pkg['post_error'] = new_err
    print 'Current Error: ' + str(new_err)

    #Find the change in error
    del_err = {}
    for tag in kwargs['scope']:
        del_err[tag] = new_err[tag] - cur_err[tag]
    print 'Change in error:'
    print del_err
    #Add change in error to package
    dakota_pkg['error_change'] = del_err

    return dakota_pkg

#Insert Dakota report into MongoDB
#Report should be formatted as a dictionary to be converted to json
def insert_document(report):
    #retrieve default local mongo instance
    client = MongoClient()
    #Connect to our 'dakota' database
    db = client['dakota']
    col = db['test_optimize']
    posts = col.posts
    #insert and get ID
    post_id = posts.insert_one(report).inserted_id
    client.close()
    return post_id

#Retrieve most recent document inserted
def retrieve_document(key_val):
    client = MongoClient()
    #Connect to our 'dakota' database
    db = client['dakota']
    col = db['test_optimize']
    posts = col.posts
    #get document based on key val
    doc = posts.find_one(key_val)
    doc_fix = {}
    #remove unicode encoding
    #for entry in doc.keys():
    #   if (entry != '_id' and entry != 'range'):
    #        doc_fix[str(entry)] = doc[entry].encode('ascii','ignore')
    #    elif (type(doc[entry]) is dict):
    #        doc_fix[str(entry)] = {}
    #        for item in doc[entry].keys():
    #            doc_fix[str(entry)][str(item)] = doc[entry][item]
    #    else:
    #        doc_fix[str(entry)] = doc[entry]
    #        print type(doc[entry])
    
    
    client.close()
    return doc

#will find find all documents with certain key values
def find_documents(key_vals):
    client = MongoClient()
    #Connect to our 'dakota' database
    db = client['dakota']
    col = db['test_optimize']
    posts = col.posts
    return posts.find(key_vals)
#get document based on key val


#Initially add the GIPL model into the db
#insert_document(GIPL)
#print retrieve_document({'model_id':'GIPL','type':'model'})

#Test Document Generation...
#dPy.random_seed(GIPL)
