from datetime import datetime

from flask import Flask, flash, redirect, render_template, url_for


app = Flask(
    __name__,
    template_folder="App/Templates",
    static_folder="App/Templates/Static",
)
app.secret_key = "local-preview-key"


EVENTS = [
    {
        "event_id": "coding-workshop",
        "name": "Campus Coding Workshop",
        "category": "Workshop",
        "date": "September 3, 2026",
        "location": "Innovation Lab",
        "available_spaces": 24,
        "registration_count": 16,
        "description": "Build a small web app with other students and campus mentors.",
        "image_url": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "event_id": "football-tournament",
        "name": "Interfaculty Football Tournament",
        "category": "Sports",
        "date": "September 8, 2026",
        "location": "Main Campus Field",
        "available_spaces": 40,
        "registration_count": 56,
        "description": "Cheer for your faculty or register to join a tournament team.",
        "image_url": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "event_id": "club-fair",
        "name": "Student Club Fair",
        "category": "Social",
        "date": "September 12, 2026",
        "location": "Central Courtyard",
        "available_spaces": 120,
        "registration_count": 82,
        "description": "Meet student communities and find the right campus club for you.",
        "image_url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=1200&q=80",
    },
]


@app.context_processor
def inject_preview_context():
    return {"instance_id": "local-preview"}


@app.get("/")
def homepage():
    categories = sorted({event["category"] for event in EVENTS})
    return render_template(
        "index.html",
        events=EVENTS,
        categories=categories,
        now=datetime.now().strftime("%B %d, %Y at %H:%M"),
    )


@app.get("/events/<event_id>")
def event_detail(event_id):
    event = next((item for item in EVENTS if item["event_id"] == event_id), None)
    return render_template("event_detail.html", event=event), 200 if event else 404


@app.post("/events/<event_id>/register")
def register_interest(event_id):
    event = next((item for item in EVENTS if item["event_id"] == event_id), None)
    if event is None:
        flash("That event could not be found.", "error")
        return redirect(url_for("homepage"))

    event["registration_count"] += 1
    event["available_spaces"] = max(0, event["available_spaces"] - 1)
    flash("You are registered for this event.", "success")
    return redirect(url_for("event_detail", event_id=event_id))


if __name__ == "__main__":
    app.run(debug=True, port=5001, use_reloader=False)
