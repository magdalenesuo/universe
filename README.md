## Components

* Flask Server - The server to make the backend for the API
* APIs - RESTful API
* Database - PostgreSQL for database


## Endpoints
### Create:
Name | Endpoint
------------ | -------------
universe :milky_way: | **/universe/<universe_id>/families**
family :family: | **/universe/<universe_id>/families**
person :bust_in_silhouette: | **/family/<family_id>/people**

### Patch/Delete:
Name | Endpoint
------------ | -------------
universe :milky_way: | **/universe/<universe_id>**
family :family: | **/family/<family_id>**
person :bust_in_silhouette: | **/person/<person_id>**

### Check particular family's power in all universe: [GET]

```
/families/check/<family_name_identifier>
```

### Fix all unbalanced family:[GET]

```
/families/fix
```
   
