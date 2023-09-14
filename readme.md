# Please Read this before running this project
I just wanted to share a quick note about model design. After some consideration, I realized that using Redis cache for tracking request count would be a better option. Unlike querying the database every time we want to update the count, Redis cache allows us to store and retrieve data much faster, resulting in improved performance.
I thought it was important to mention this in the project, specifically in a place other than the readme.md file. 
## Django Onefin assignment

This is a Django project that requires Redis. Follow the instructions below to set up and run the project.
Make sure youe redis server is running before running django server.

## Import this Json in postman
This file has all API request you can import this file in postman.</br>
[API List (Onefin.postman_collection.json)](./Onefin.postman_collection.json)

## Installation

1. Clone the repository:

```bash
   git clone https://github.com/ransom12/onefin.git
```
2. Install requirements.txt 
```bash
   pip install -r requirements.txt
```
3. Make migrations and migrate
```bash
   python manage.py makemigrations && python manage.py migrate 
```
4. Now Runserver
```bash
   python manage.py runserver
```
5. To run test case
```bash
   python manage.py test
```