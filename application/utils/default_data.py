
from uuid import uuid4
from sqlalchemy.orm.session import Session 

from application.permission.models import Role
from application.session.models import User, Principals
from application.session import controller as user_controller
from application.utils.db_connection import session_hook

roles = [
    { "code": "admin", "name": "Administrator", "key": 1},
    { "code": "pm", "name": "Project Manager", "key": 2},
    { "code": "deo", "name": "Data Entry Officer", "key": 3},
    { "code": "basic", "name": "Basic", "key": 4},
    { "code": "guest", "name": "Guest", "key": 5}
]


@session_hook
def create_roles(db: Session) -> None:
    i = 0
    objects = []
    for role in roles:
        i = i + 1
        if Role.get_role_by_code(db, role['code']) == None:
            objects.append(Role(**role))
    db.bulk_save_objects(objects)
    db.flush()


@session_hook
def create_admin_user(db: Session) -> None:
    existing_user = User.get_user_by_username(db, "admin")
    if existing_user in ["", None]:
        user = User()
        user.first_name = "Administrator"
        user.last_name = "Admin"
        user.username = "admin"
        user.email = "admin@rimscloud.co"
        user.active = True
        user.is_verified = True
        user.approved = True
        user.password = user_controller.pwd_context.hash("admin")
        p1 = Principals(**{"value": "role:admin"})
        p2 = Principals(**{"value": f"role:{user_controller.DEFAULT_ROLE}"})
        user.principals.append(p1)
        user.principals.append(p2)
        user.uuid = str(uuid4())
        db.add(user)
        db.flush()


# call the methods to create the items. 
def run():
    create_roles()
    create_admin_user()


