 Dakota to Python interface for model Optimization
=================================================
Requirements:
-------------
* Dakota 6.3.0 Installed
* Python 2.7
* Anaconda (Numpy)

GIPL Model Optimization 
-----------------------
Run dPy example:
1. git clone into GIPL model folder
2. Run `python dpy_examples.py` in command line to initiate example.


### Working with Dakota
  Generally all one needs to use dakota is to create a .in file with the proper
  syntax.

  Here is an example of a properly formatted .in file
```
environment
	tabular_data
	tabular_data_file = 'dakota_temp.dat'
method 
 efficient_global 
 seed=314159
 
model single

variables
continuous_design = 6
initial_point 1.036500809 0.8026228473 1.237922959 1.449840745 1.301039856 2.214932838
lower_bounds 0.936500809 0.7026228473 1.137922959 1.349840745 1.201039856 2.114932838
upper_bounds 1.136500809 0.9026228473 1.337922959 1.549840745 1.401039856 2.314932838
descriptors 'k1' 'k2' 'k3' 'k4' 'k5' 'k6'

interface,
fork
   analysis_drivers = 'objective_function.py'
parameters_file = 'params.in'
results_file = 'results.out'

responses
objective_functions = 1
no_gradients
no_hessians
```
 Note how the file is seperated into sections which define settings for Dakota's behavior

**Method**

 The method section specifies what type of action Dakota will take with the objective function.
 Some methods that I have found useful for the GIPL model are as follows.

###### Global Optimization

 coliny_ea
 :  Genetic optimization technique treating inputs as genetic code that goes through natural selection for a minimized objective function. This method is *slow* yet effective.

 mesh_adaptive_search
 :  This method generates a mesh of points within the constraint boundaries and iteratively increases the density of the points untill they converge onto a minimum objective function value.

###### Local Optimization
 
 conmin_frcg
 :  This is a simple gradient based optimization technique that can use numerical gradients to converge on a local minimum. Note, this method may be innacurate with non-sensitive parameters.

 vector_parameter_study
 : This method will sample along a given vector and is useful for when gradient based techniques are failing. This is most effective in 1D

 ##### Interface
 The Interface section tells dakota what model to link to and how to communicate with it.
 To use an outside model one must use the `fork` keyword as in the snippet below.
```
interface,
fork
   analysis_drivers = 'objective_function.py'
parameters_file = 'params.in'
results_file = 'results.out'
```
 The `analysis_drivers` parameter is the name of your objective function script.
 The `parameters_file` is what the objective function must read in to get the inputs for the model. The `results_file` is what the objective function must output in the proper format for Dakota to interpret.

### Installing MongoDB database
Follow this [link](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-os-x/) to find installation instructions for MongoDB. I recommend using the homebrew method as it is the simplest.

### Linking a Model to dPy
Below is an example of the format for linking a numerical model to dPy.
``` Python
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

```
The `model_id` tag is used to later link the model to dakota analysis. The `driver_path` tag is the path of the objective function. The 'params' tag is the path to the file that the numerical simulation reads its parameters from. The `syn_params` tag is the path to the file that the paremeters which generated the synthetic data are stored. The `sim_out` tag is the path to the file which holds the simulation out data. The `syn_out` tag is the path to the file that has the sythetic truth simulation out data. The `schema` file is a special file that holds the structure and gives variable key names to the parameters in the `params` file. Observe the schema file for the GIPL model.
```
* a1 b1 * * kt1 kf1 *
* a2 b2 * * kt2 kf2 *
* a3 b3 * * kt3 kf3 *
* a4 b4 * * kt4 kf4 *
* a5 b5 * * kt5 kf5 *
* a6 b6 * * kt6 kf6 *

```
Indicate the position that a certain parameter is in by placing its identifier in its spot in the file. To indicate that a number in a parameter file should not be interpreted as anything simply place a * in its spot.

### Generating dPy Reports

Dakota is treated as a 3rd party service that is interacted with via the dakota_report library allowing dakota operations such as optimization and parameter studies and then storing the output from them.

This example will use a genetic optimization algorithm to find an approximate global min and equillibrium in the objective function. It will then begin a 1D parameter study on each coefficient about the point to investigate equillibrium behavior.
``` Python
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

```
Here we define our two different dakota analysis methods `gene_report` for genetic optimization and `param_study` for a 1-D parameter study. Note how they are both linked by the `group` tag. The group tag makes retrieval of diagnostic reports simple as one can simply make a query for all reports of a specified group tag. The `scope` tag specifies the variables that are being used for a certain dakota action. The variables used should be passed within an array and appear within the model's schema file. 
```
#call 'execute_dakota' with a genetic optimiaz
#gene_report = dr.execute_dakota(**gene_report)
#insert genetic report into database
#dr.insert_document(gene_report)
```
From the dakota_report library call `execute_dakota(**<REPORT_NAME>)` to perform a dakota operation and have the diagnostics package passed back as a Python dictionary. To insert one of these reports into the local MongoDB database pass it into the `insert_document()` function.
```
#OR... Retrieve the report from the database
gene_report = dr.retrieve_document({'group':'Genetic_param_study','method':'genie_direct'})
```
One can retrieve this report from database using the `retrieve_document()` function, where we pass in the key vals `{'group':'Genetic_param_study','method':'genie_direct'}` to get the report from the `genetic_param_study` group that used the `genie_direct` genetic optimization method.
```
#Retrieve the optimized post parameters from the report
gene_params = gene_report['post_params']
#remove obj_fun parameter
gene_params.pop('obj_fn',None)
#Set the param studys' seed
param_study['seed_pt'] = gene_params
```
From the genetic report we can retrieve the optimized post parameters with the `post_params` key. We then set the parameter study's seed point to these parameters by changing param_study's `seed_pt` key.

```
#Iterate through parameters performing 1D parameter studies
for param in gene_params.keys():
    #Change param_study scope
    param_study['scope'][0] = param
    #Perform parameter study
    print 'STARTING PARAM STUDY FOR ' + param
    param_report = dr.execute_dakota(**param_study)
    #Insert report into database
    dr.insert_document(param_report)
```
Now that we have set this report's seed to the approximate equilibrium found by the genetic optimization, we can cycle through every key in the parameter list and one by one change the parameter study's scope to that key and then run a seperate parameter study for each one.

The results of this parameter study can be viewed [here.s](https://github.com/JasonCyrus/dakota-tools/blob/master/Visualize_Report.ipynb)
