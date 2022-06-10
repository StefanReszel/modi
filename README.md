# MODi - My Own Dictionary

## Description
MODi is a learning platform, that allows users to
create their own dictionaries in the groups, which are
created by themselves as well. To use MODi it is
necessary to register and to be logged in. There is
permited to edit credentials, except username, and all
records of database. Logic of learning is performed
on client side and it's implement in JavaScript.

## Technologies
<ul>
<li>Python</li>
<li>Django</li>
<li>Django REST framework</li>
<li>PostgreSQL</li>
<li>Celery</li>
<li>Redis</li>
<li>Docker</li>
<li>Docker Compose</li>
<li>HTML, CSS, JavaScript</li>
</ul>

## Setup
The fastest and the most convenient way to run MODi is to use Docker Compose.
<br>
Firstly clone the repo
```
git clone https://github.com/StefanoDaReel/modi.git
```
Next, ensure you have Docker Compose installed, if not check the site <a href="https://docs.docker.com/compose/install/">https://docs.docker.com/compose/install/</a>
<br>
Now, from the app directiory(which contains docker-compose.yml file) run command:
```
docker-compose up -d
```
Another step is to make migrations to database, run these commands:
```
docker-compose exec modi python manage.py makemigrations
```
```
docker-compose exec modi python manage.py migrate
```
Last thing to is to restart container where the MODi is running:
```
docker-compose restart modi
```
In your browser, go to <a href="http://localhost:8000/">http://localhost:8000/</a>
<br>
Enjoy!
<br>
You can also check it out <a href="https://agile-beyond-46801.herokuapp.com/">here.</a>
