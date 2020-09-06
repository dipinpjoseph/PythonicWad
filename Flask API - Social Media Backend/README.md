# Python/Flask Backend Task - Irithm
The Flask application is currently hosted on a raspberry pi at [https://pi.thebearsenal.com/](https://pi.thebearsenal.com/).

## Initialization
 - All pip dependencies are stored in requirements.txt. 
 - Virtual environment created in Python3.8 naming 'irithm-env'. 
 - The shell script run.sh will start the Flask server. 
 - app/\_\_init\_\_.py contains necessary configurations.
## Database Design
The PostgreSQL databased in named as "db_irithm" and contains 8 tables.
### Summary
#### users
Details of users. Undergoes many to many relationships with tables __roles__ and __list_roles__.
#### roles
Stores details about available user roles.
#### user_roles
Assosiation table between __roles__ and __users__.
#### lists
Stores lists ans related cards. Follows one to many  relationship with __cards__ and many to many relation with __users__.
#### list_roles
Assosiation table beween __lists__ and __users__.
#### cards
Stores details of each card and follows one to many relationship with __comments__.
#### comments
Stores details of each comment and user, follows one to many relationship with __replies__.
#### replies
Stores details of each reply and it's owner.
## API Usage 
## User Management
### Signup (/users/signup)
A new user can be registered in member role.
**Request Type** - POST
**Params** - username, email, password
### Login (/users/login)
**Request Type** - POST
**Params** -  email, password
### Logout (/users/logout)
**Request Type** - POST
**Params** -  none
### List Users (Admin) (/users)
**Request Type** - GET
**Params** -  none
## Role Management
### Initial roles (One time request) (/users/role)
**Request Type** - GET
**Params** -  none
### Add/Update Role (Admin)(/users/role)
**Request Type** - POST, DELETE
**Params** -  email, role
## List Management
### Get/Add/Update/Delete list  (/lists)
**Request Type** - GET,POST, PUT,DELETE
**Params** 
GET - none
POST - name
PUT - id,name
DELETE - id
### Show list and nested cards (/lists/show)
**Request Type** - POST
**Params**  - id
## List Roles Management
### View/Assign/Unassign list-user  (Admin) (/lists/roles)
**Request Type** - GET,POST,DELETE
**Params** 
GET - none
POST - user_id, lists_id
DELETE - user_id, lists_id
## Cards Management
### View/Create/Update/Delete cards (/cards)
**Request Type** - GET,POST, PUT,DELETE
**Params** 
GET - none
POST - title,desc,lists_id
PUT - id,title,desc,lists_id
DELETE - id
### Show card and 3 comments (/cards/show)
**Request Type** - POST
**Params**  - id
## Comments Management
### View/Create/Update/Delete comments (/comments)
**Request Type** - GET,POST, PUT,DELETE
**Params** 
GET - none
POST - content,cards_id,user_id
PUT - id,content,cards_id,user_id
DELETE - id
### Show comment and replies (/comments/show)
**Request Type** - POST
**Params**  - id

**Note: For larger databases query can be made faster with database indexing and database shredding.**
