note from fastapi template

env root dir

requirements.txt scoped to root of backend dir

use **init**.py to specify package as module

endpoint names are nouns not verbs i.e (/users ) AVOID (/getUsers)

plural resource names /items

nest related resources under parent /users/{userId}/orders/{orderId}

filtering/pagination/sorting go in query param GET /projects?status=active&page=2&per_page=20

keep words lower case and hyphentated for multiple words /user-profiles

use correct http method (put and patch)
