from flask import Blueprint, render_template, redirect, url_for, session
from utils.json_manager import load_notices

notice_bp = Blueprint("notice", __name__, url_prefix="/notice")


@notice_bp.route("/")
def list_notices():
    notices = load_notices()
    pinned  = [n for n in notices if n.get("pinned")]
    regular = sorted(
        [n for n in notices if not n.get("pinned")],
        key=lambda x: x["id"], reverse=True
    )
    return render_template("notice/list.html", notices=pinned + regular)


@notice_bp.route("/<int:notice_id>")
def detail(notice_id):
    notices = load_notices()
    notice  = next((n for n in notices if n["id"] == notice_id), None)
    if not notice:
        return redirect(url_for("notice.list_notices"))
    return render_template("notice/detail.html", notice=notice)
