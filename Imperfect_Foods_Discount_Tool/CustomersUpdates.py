import smtplib
import requests
import os
from dotenv import load_dotenv

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")

pushover_url = "https://api.pushover.net/1/messages.json"


def push(text):
    requests.post(
        pushover_url,
        data={
            "token": pushover_token,
            "user": pushover_user,
            "message": text,
        },
    )

# def Customer_updates(item):
#     if item['category'] == intrest_customers['category']:
#         message = f"Hi {intrest_customers['email']}, we would like to inform you that there are some {intrest_customers['category']} available near to your location with a good discount."
#         email_sender = ''
#         email_receiver = ''


def record_unknown_question(question):
    push(f"Recording {question} asked that I couldn't answer")
    return "OK"

def record_user_details(email, name = "Not provided", notes = 'Not provided'):
    push(f'Record an interest from {email}, his name is {name} and notes {notes}')
    return "Done"

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {"type": "string", "description": "Any additional info about the conversation that's worth recording to give context"
            }
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question that couldn't be answered"},
        },
        "required": ["question"],
        "additionalProperties": False
    }
}
