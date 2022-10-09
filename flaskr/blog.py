from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("blog", __name__)


@bp.route("/",methods=("GET", "POST"))
@login_required
def index():
    db = get_db()
    stars = db.execute("SELECT post_id, COUNT(*) AS kfklkdl"
                       " FROM star"
                       " GROUP BY post_id").fetchall()
    stars2 = db.execute("SELECT post_id, user_id"
                        " FROM star").fetchall()
    print(stars)
    if request.method=="POST":
        print("dklglkdfj")
        search_content = str(request.form["search_content"])
        print(type(search_content))
        posts = db.execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.body= ?"
            " ORDER BY created DESC",search_content
        ).fetchall()
    else:
        posts = db.execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " ORDER BY created DESC"
        ).fetchall()


    return render_template("blog/index.html", posts=posts,stars=stars,stars2=stars2)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)

@bp.route("/<int:id>/star")
@login_required
def star(id):
    """Star a post for the current user, or unstar if already starred."""
    post = get_post(id, check_author=False)
    db = get_db()
    error = None

    if post["author_id"] == g.user["id"]:
        error = "You cannot star your own post."

    if error is not None:
        flash(error)
    else:
        if db.execute(
            "SELECT 1 FROM star WHERE post_id = ? AND user_id = ?", (id, g.user["id"])
        ).fetchone() is not None:
            db.execute("DELETE FROM star WHERE post_id = ? AND user_id = ?", (id, g.user["id"]))
        else:
            db.execute("INSERT INTO star (post_id, user_id) VALUES (?, ?)", (id, g.user["id"]))


        db.commit()
    return redirect(url_for("blog.index"))
@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))
