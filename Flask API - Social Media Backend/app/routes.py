from app import app, login_manager
from models import Users, Role, UserRoles, db, Lists, ListRoles, Cards, Comments, Replies
from flask import request, jsonify,render_template
import json
from flask_user import roles_required
from flask_login import current_user, login_user, logout_user, login_required

# Initial setup for Roles
@app.route('/users/role', methods=['GET'])
def create_role():
    admin_role = Role('Admin')
    mem_role = Role('Member')
    db.session.add(admin_role)
    db.session.add(mem_role)
    db.session.commit()
    return("Roles Created")

# Update User Roles
@app.route('/users/role', methods=['POST','DELETE'])
@login_required
def update_role():
    req = json.loads(json.dumps(request.get_json()))
    user = Users.query.filter_by(email=req["email"]).first()
    if not (admin_check(current_user.id)):
        return ("401: Unauthorized")
    mem_role = Role.query.filter_by(name=req["role"]).first()
    if request.method == 'DELETE':
        user.roles.remove(mem_role)
    else:
        user.roles.append(mem_role)
    db.session.commit()
    return("Role Updated")

# Add user as Member Role
@app.route('/users/signup', methods=['POST'])
def create_user():
    req = json.loads(json.dumps(request.get_json()))
    user = Users()
    user.username = req["username"]
    user.email = req["email"]
    mem_role = Role.query.filter_by(name='Member').first()
    user.roles.append(mem_role)
    user.password = req["password"]
    db.session.add(user)
    db.session.commit()
    return("Sucess")

# User Login
@app.route('/users/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return ("User already logged in")
    req = json.loads(json.dumps(request.get_json()))
    user = Users.query.filter_by(email=req["email"]).first()
    if user is None or user.password != req["password"]:
        return("Login Failed")
    else:
        login_user(user, remember=True)
        return("Successfully logged in")

# User Logout
@app.route('/users/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return("Successfully logged out")

# All users list
@app.route('/users',methods=['GET'])
@login_required
def all_users():
    if not (admin_check(current_user.id)):
        return ("401: Unauthorized")
    if request.method == "GET":
        t_list = []
        for data in Users.query.all():
            t_list.append(data.as_dict())
        return jsonify(t_list)


# Fetching user object
@login_manager.user_loader
def load_user(id):
    return (Users.query.get(int(id)))

def admin_check(id):
    if bool(UserRoles.query.filter_by(user_id = id, role_id = 1).first()):
        return (True)
    else:
        return (False)

# Add List 
@app.route('/lists',methods=['GET','POST','PUT','DELETE'])
@login_required
def curd_list():
    req = json.loads(json.dumps(request.get_json()))
    if request.method == "GET" and admin_check(current_user.id):
        t_list = []
        for data in Lists.query.all():
            t_list.append(data.as_dict())
        return jsonify(t_list) 
    if admin_check(current_user.id) and request.method == "POST":
        lists = Lists()
        lists.name = req["name"]
        db.session.add(lists)
        db.session.commit()
        return("List Created")
    if (int(req["id"]) in mem_access(current_user.id)["list"]):
        if request.method == "PUT":
            lists = Lists.query.filter_by(id=req["id"]).first()
            lists.name = req["name"]
        if request.method == "DELETE":
            lists = Lists.query.filter_by(id=req["id"]).delete()
        db.session.commit()
        return ("Operation Completed")
    return("401: Unauthorized")

@app.route('/lists/show',methods=['POST'])
@login_required
def show_list():
    req = json.loads(json.dumps(request.get_json()))
    if (int(req["id"]) not in mem_access(current_user.id)["list"]):
        return("401: Unauthorized")
    cards = Cards.query.filter_by(lists_id=req["id"]).all()
    t_list = []
    t_list.append(Lists.query.filter_by(id=req["id"]).first().as_dict())
    for data in cards:
        t_list.append(data.as_dict())
    return jsonify(t_list)

# Update List Roles
@app.route('/lists/roles',methods=['GET','POST','DELETE'])
@login_required
def curd_list_roles():
    if not (admin_check(current_user.id)):
        return ("401: Unauthorized")
    if request.method == "GET":
        t_list = []
        for data in ListRoles.query.all():
            t_list.append(data.as_dict())
        return jsonify(t_list)
    req = json.loads(json.dumps(request.get_json()))
    if request.method == "POST":
        list_roles = ListRoles()
        list_roles.user_id = req["user_id"]
        list_roles.lists_id = req["lists_id"]
        db.session.add(list_roles)
    if request.method == "DELETE":
        ListRoles.query.filter_by(user_id=req["user_id"],lists_id=req["lists_id"]).delete()
    db.session.commit()
    return ("List Roles operation Successfull")
       
# Cards operations
@app.route('/cards',methods=['GET','POST','PUT','DELETE'])
@login_required
def curd_cards():
    req = json.loads(json.dumps(request.get_json()))
    if request.method == "GET" and admin_check(current_user.id):
        t_list = []
        for data in Cards.query.all():
            t_list.append(data.as_dict())
        return jsonify(t_list) 
    elif not "lists_id" in req:
        return ("400: Bad Request")
    elif (int(req["lists_id"]) in mem_access(current_user.id)["list"]) or admin_check(current_user.id):
        if request.method == "POST":
            cards = Cards()
            cards.title = req["title"]
            cards.description = req["desc"]
            cards.lists_id = req["lists_id"]
            db.session.add(cards)
        if request.method == "PUT":
            cards = Cards.query.filter_by(id=req["id"]).first()
            cards.title = req["title"]
            cards.description = req["desc"]
            cards.lists_id = req["lists_id"]
        if request.method == "DELETE":
            Cards.query.filter_by(id=req["id"]).delete()
        db.session.commit()
        return ("Card operation completed successfully")
    else:
        return ("401: Authorization Error")

# Show cards with comments
@app.route('/cards/show',methods=['POST'])
@login_required
def show_cards():
    req = json.loads(json.dumps(request.get_json()))
    if (int(req["id"]) not in mem_access(current_user.id)["cards"]):
        return("401: Unauthorized")
    comments = Comments.query.filter_by(cards_id=req["id"]).limit(3).all()
    t_list = []
    t_list.append(Cards.query.filter_by(id=req["id"]).first().as_dict())
    for data in comments:
        t_list.append(data.as_dict())
    return jsonify(t_list)


# Comments operations
@app.route('/comments',methods=['GET','POST','PUT','DELETE'])
@login_required
def curd_comments():
    req = json.loads(json.dumps(request.get_json()))
    if request.method == "GET" and admin_check(current_user.id):
        t_list = []
        for data in Comments.query.all():
            t_list.append(data.as_dict())
        return jsonify(t_list) 
    elif not "cards_id" in req:
        return ("400: Bad Request")
    if (int(req["cards_id"]) in mem_access(current_user.id)["cards"]) or (admin_check(current_user.id)):
        if request.method == "POST":
            comments = Comments()
            comments.content = req["content"]
            comments.cards_id = req["cards_id"]
            comments.user_id = req["user_id"]
            db.session.add(comments)
        if request.method == "PUT":
            comments = Comments.query.filter_by(id=req["id"]).first()
            comments.content = req["content"]
            comments.cards_id = req["cards_id"]
            comments.user_id = req["user_id"]
        if request.method == "DELETE":
            Comments.query.filter_by(id=req["id"]).delete()
        db.session.commit()
    return ("Request Processed")

# Replies Operations
@app.route('/replies',methods=['POST','PUT','DELETE'])
@login_required
def curd_replies():
    req = json.loads(json.dumps(request.get_json()))
    if (int(req["comment_id"]) not in mem_access(current_user.id)["comments"]):
        return("401: Unauthorized")
    if request.method == "POST":
        replies = Replies()
        replies.replies = req["replies"]
        replies.user_id = req["user_id"]
        replies.comment_id = req["comment_id"]
        db.session.add(replies)
    if request.method == "PUT":
        replies = Replies.query.filter_by(id=req["id"]).first()
        replies.replies = req["replies"]
        replies.user_id = req["user_id"]
        replies.comment_id = req["comment_id"]
    if request.method == "DELETE":
        Replies.query.filter_by(id=req["id"]).delete()
    db.session.commit()
    return ("Replies operation completed successfully")

# Show comments with replies
@app.route('/comments/show',methods=['POST'])
@login_required
def show_comments():
    req = json.loads(json.dumps(request.get_json()))
    if (int(req["id"]) not in mem_access(current_user.id)["comments"]):
        return("401: Unauthorized")
    replies = Replies.query.filter_by(comment_id=req["id"]).all()
    t_list = []
    t_list.append(Comments.query.filter_by(id=req["id"]).first().as_dict())
    for data in replies:
        t_list.append(data.as_dict())
    return jsonify(t_list)


# Fetching all list and subsidary access of a member
def mem_access(id):
    l_roles = ListRoles.query.filter_by(user_id=id).all()
    access = {}
    list_access = []
    cards_access = []
    comments_access = []
    replies_access = []
    for role in l_roles:
        list_access.append(int(role.lists_id))
        for card in Cards.query.filter_by(lists_id=int(role.lists_id)).all():
            cards_access.append(int(card.id))
            for comment in Comments.query.filter_by(cards_id=card.id).all():
                comments_access.append(comment.id)
                for reply in Replies.query.filter_by(comment_id=comment.id).all():
                    replies_access.append(reply.id)
    access["list"] = list_access
    access["cards"] = cards_access
    access["comments"] = comments_access
    access["replies"] = replies_access
    return(access)

@app.route('/')
def root():
    return render_template('Index.html')
