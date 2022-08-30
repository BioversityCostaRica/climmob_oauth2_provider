ClimMob OAuth2 Provider
==============

This plug-in adds functionality for ClimMob to act as an OAuth2 provider. 

Getting Started
---------------

- Activate the ClimMob environment.
```
$ . ./path/to/ClimMob/bin/activate
```

- Change directory into the plug-in directory.
```
$ cd OAuth2Provider
```

- Build the plugin
```
$ python setup.py develop
```

- Alembic configuration for extra tables
```
$ mv alembic.example.ini alembic.ini
```
- Edit the alembic.ini an replace sqlalchemy.url with the one in the FormShare ini file
```    
$ alembic upgrade head
```

- Add the plugin to the ClimMob list of plugins by editing the following line in development.ini or production.ini
```
    #climmob.plugins = examplePlugin
    climmob.plugins = OAuth2Provider
```

- Run ClimMob again. The functionality that this plug-in adds to ClimMob is only accessible to the user administrator of ClimMob
