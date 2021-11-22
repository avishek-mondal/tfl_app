# TFL scheduler

## Brief description

The app has 3 main components

1. A store (in `store.py`). This is where results from the API for the tasks generated is stored. 
   1. The important class here is the `AbstractMemoryStore` class. Any subclasses of this can be plugged into the
    rest of the components. 
      1. For a quick implementation, I have implemented `InMemoryStore`, and that is the default store for the app. It basically consists of 2 dicts, and naturally, if the docker container running the application is closed, all values stored in these dicts will be deleted. 
         1. Given the quirks of the `FlaskView` class (mentioned later) the `InMemoryStore` has to be a singleton
      2. To demonstrate how a SQL store can be implemented an example of `SQLStore`, which shows how a postgresql database can be used as a store as well. If we are to scale this app to use some kind of cloud store, for example an AWS RDS instance of a postgresql database, the connections and implementations of methods will be similar 
2. A scheduler (in `tfl_scheduler.py`)
   1. This class basically customises the `apscheduler` library available in python.
   2. The main method that we schedule at the given times is the `get_from_tfl` method in `tfl_scheduler.py`
3. The actual server itself in `run.py`
   1.  `TflAppServer` inherits from `FlaskView`. Ideally, it should be a simple http server, i.e. inherit from the `HTTPServer` class, but for a quick implementation that still leaves room for minimal refactoring when scaling up later on, inheriting from `FlaskView` seemed to be the easiest thing to do
   2.  The `__init__` method in a `FlaskView` instance is called for every public route (in our case - 3) of the app, which is why the `InMemoryStore` has to be a singleton.

## Usage instructions 

### Starting the server

To run locally: 

1. Open a terminal, navigate to the same directory as this readme and run `FLASK_APP=run FLASK_DEBUG=1 flask run`

### Using Docker 

1. From inside the current directory, run `docker build -t tfl_app_img .`
   1. This will build the image, and name it `tfl_app_img`

2. To run an instance of the image, run `docker run -p 5000:5000 --name tfl_app tfl_app_img`


### Submitting requests

Example - say you want to post a task now. Run the following curl command - 

```
curl -X POST -d "lines=bakerloo,jubilee" http://localhost:5000/tasks
```

In terminal, the output would be 

```
Successfully posted. Task id is 75c2a0ccfae94ea48fe2dbc47022e874
```

Then, to get the results of this task, you would then do 

```
response from api is [{'$type': 'Tfl.Api.Presentation.Entities.Disruption, Tfl.Api.Presentation.Entities', 'category': 'RealTime', 'type': 'lineInfo', 'categoryDescription': 'RealTime', 'description': 'Bakerloo Line: Service will resume later this morning. ', 'affectedRoutes': [], 'affectedStops': [], 'closureText': 'serviceClosed'}, {'$type': 'Tfl.Api.Presentation.Entities.Disruption, Tfl.Api.Presentation.Entities', 'category': 'RealTime', 'type': 'lineInfo', 'categoryDescription': 'RealTime', 'description': 'Jubilee Line: Service will resume later this morning. ', 'affectedRoutes': [], 'affectedStops': [], 'closureText': 'serviceClosed'}]
```

You can specify a scheduled time as follows - 

```
curl -X POST -d "schedule_time=2021-12-01T02:30:40&lines=bakerloo,jubilee" http://localhost:5000/tasks
```

to get 

```
Successfully posted. Task id is 2b6dc68736f24fcdb8b53f7ce144649c
```

The results of this task will only be available after the scheduled time. 

You can also list all the tasks with 

```
curl -X GET http://localhost:5000/tasks
```

and the output is - 

```
{
  "75c2a0ccfae94ea48fe2dbc47022e874": [
    {
      "$type": "Tfl.Api.Presentation.Entities.Disruption, Tfl.Api.Presentation.Entities", 
      "affectedRoutes": [], 
      "affectedStops": [], 
      "category": "RealTime", 
      "categoryDescription": "RealTime", 
      "closureText": "serviceClosed", 
      "description": "Bakerloo Line: Service will resume later this morning. ", 
      "type": "lineInfo"
    }, 
    {
      "$type": "Tfl.Api.Presentation.Entities.Disruption, Tfl.Api.Presentation.Entities", 
      "affectedRoutes": [], 
      "affectedStops": [], 
      "category": "RealTime", 
      "categoryDescription": "RealTime", 
      "closureText": "serviceClosed", 
      "description": "Jubilee Line: Service will resume later this morning. ", 
      "type": "lineInfo"
    }
  ]
}

```


## Miscellaneous

### Generating `requirements.txt`

I used pipreqs to generate `requirements.txt`.

1. `pip install pipreqs`

2. `pipreqs . --force`

