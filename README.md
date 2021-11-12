# Configuration File in detail:

Below is the description of ibot_dag_orch.py configuration parameters

### probability of failure parameter:
| param | description |
| ------- | ------- |
| beta | probability of failure threshold |
| gamma | maximum number of replication allowed for each task | 

### Edge Device parameters:

| param | description|
| ------- | ----- |
| lambda[] | plot of probability of failure for edge device |
| num_edge | number of edge devices will be used in the simulation |

### Simulation parameters:

｜ param | description |
｜ ----- | ----------- |
| ntbd | network bandwidth |
| app_inst_name | the simulation time during when the task arrives randomly |
| num_arrivals | number of task arrive during app_inst_name |
| sim_time | simulation period (this need to be tuned to accomodate the random generated task arrivals) |
