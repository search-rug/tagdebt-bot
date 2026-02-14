import os
import requests
import json
import base64
import hmac

from flask import Flask, request, abort
from github import Github, GithubIntegration
from apscheduler.schedulers.background import BackgroundScheduler
from emailSender import send_email
from lingeringIssuesProcessor import process_lingering_issues

app = Flask(__name__)

github_app_id = 821348

# Read the bot certificate
with open("bot_key.pem", "r") as cert_file:
    github_app_key = cert_file.read()

# Create a GitHub integration instance
git_integration = GithubIntegration(
    github_app_id,
    github_app_key,
)

# Get the list of installations of the bot's GitHub App
installations = git_integration.get_installations()

repositories_info = []

# Obtain details about each installation
for installation in installations:
    # Obtain the id of each installation of the GitHub App
    installation_id = installation.id
    # Obtain the repositories where the bot is installed
    repositories = installation.get_repos()
    for repository in repositories:
        """
        Create a list containing the repositories where the bot is installed, the owners of the repositories, and the
        id of each of the installations of the GitHub App.
        """
        repositories_info.append((repository.name, repository.owner.login, installation_id))

# Scheduling the processing of lingering issues
scheduler = BackgroundScheduler()
# Schedule the function process_lingering_issues to run every 1 day from the moment the bot is started
lingering_check_frequency = 1
scheduler.add_job(func=process_lingering_issues, trigger='interval', days=lingering_check_frequency,
                  args=(git_integration, repositories_info, lingering_check_frequency))
scheduler.start()


def label_issue(issue, config, label=None):
    if label is None:
        # Call the model API to get the label
        url = config["endpoint"]
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        data = {}
        if config["payload-type"] == "title":
            data["text"] = issue.title
        elif config["payload-type"] == "description":
            if issue.body is not None:
                data["text"] = issue.body
            else:
                print("Issue does not have a description, no label generated", flush=True)
                return
        elif config["payload-type"] == "merged":
            data["text"] = issue.title + (" " + issue.body if issue.body is not None else "")
        elif config["payload-type"] == "both":
            label_title_and_desc(config, data, headers, issue, url)
            return
        result = requests.post(url, headers=headers, data=json.dumps(data)).json()
        label_location = config["label-location"]
        label = result[label_location]
        # Add the label to the issue
        issue.add_to_labels(label)
        # Send email if emails for labels/all types of emails are enabled in config.json
        if config["send-emails"] is True and config["when-to-send"] in ["label", "all"]:
            send_email([issue], config, 0, label)
    else:
        # Simply add the label to the issue (for custom labels)
        issue.add_to_labels(label)
        # Send email if emails for feature under development/all types of emails are enabled in config.json
        if config["send-emails"] is True and config["when-to-send"] in ["feature", "all"]:
            send_email([issue], config, 2, label)


def label_title_and_desc(config, data, headers, issue, url):
    data["text"] = issue.title
    result = requests.post(url, headers=headers, data=json.dumps(data)).json()
    label_location = config["label-location"]
    title_label = result[label_location]
    # Add the label generated for the issue title to the issue
    issue.add_to_labels("title: " + title_label)

    description_label = None
    if issue.body is not None:
        data["text"] = issue.body
        result = requests.post(url, headers=headers, data=json.dumps(data)).json()
        label_location = config["label-location"]
        description_label = result[label_location]
        # Add the label generated for the issue description to the issue
        issue.add_to_labels("description: " + description_label)
    else:
        print("Issue does not have a description, no description label generated", flush=True)

    # Send email if emails for labels/all types of emails are enabled in config.json
    if config["send-emails"] is True and config["when-to-send"] in ["label", "all"]:
        if description_label is None or title_label == description_label:
            """
            Single email (for the title label) if the issue does not contain a description (and consequently, no 
            description label is generated) or if the labels generated for both the title and the description of the 
            issue are identical
            """
            send_email([issue], config, 0, title_label)
        else:
            # Separate emails if the labels generated for the title and the description of the issue are different
            send_email([issue], config, 0, "Title: " + title_label)
            send_email([issue], config, 0, "Description: " + description_label)


def handle_issue_comment_event(repo, payload, config):
    commenter = payload["comment"]["user"]["login"]
    if commenter == "issue-classification-bot[bot]":
        return "ok"

    comment = repo.get_issue(number=payload["issue"]["number"]).get_comment(
        payload["comment"]["id"]
    )
    issue = repo.get_issue(number=payload["issue"]["number"])

    # Comment body will be a command like "/tdbot label", "/tdbot help", etc. So we need to parse it
    command = comment.body.split(" ")
    if command[0] == "/tdbot":
        if command[1] == "label":
            if len(command) == 2:
                label_issue(issue, config)
            else:
                # Add everything after the command to the label
                label = " ".join(command[2:])
                label_issue(issue, config, label)
        elif command[1] == "help":
            with open("help_message.txt", "r") as f:
                help_message = f.read()
            issue.create_comment(help_message)
        else:
            issue.create_comment("I don't understand your command. Please try again.")

    return "ok"


def handle_issue_creation_event(repo, payload, config):
    # Check if the issue is newly created
    if payload["action"] != "opened":
        return "ok"

    issue = repo.get_issue(number=payload["issue"]["number"])
    # Check if initial messages for issues is enabled in config.json
    if config["initial-message"] is True:
        issue.create_comment(
            ":robot: **Issue Classification Bot** is active on this repository.\n\n"
            'Learn what commands you can use in issues by commenting "/tdbot help"'
        )
    # Check if auto-labeling of issues is enabled in config.json
    if config["auto-label"] is True:
        label_issue(issue, config)
    # Send email if emails for feature under development/all types of emails are enabled in config.json
    if config["send-emails"] is True and config["when-to-send"] in ["feature", "all"]:
        send_email([issue], config, 2)

    return "ok"


@app.route("/webhook", methods=["POST"])
def bot():
    # Validate that the request is from GitHub
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    signature = request.headers.get("X-Hub-Signature")
    if signature is None:
        abort(403)

    sha_name, signature = signature.split("=")
    if sha_name != "sha1":
        abort(501)

    mac = hmac.new(secret.encode("utf-8"), msg=request.data, digestmod="sha1")

    if not hmac.compare_digest(str(mac.hexdigest()), str(signature)):
        abort(403)

    # Get the event payload
    payload = request.json

    # Check if the event is a GitHub issue comment creation event
    payload_type = request.headers.get("X-GitHub-Event")
    owner = payload["repository"]["owner"]["login"]
    repo_name = payload["repository"]["name"]

    # Get a git connection as our bot
    git_connection = Github(
        login_or_token=git_integration.get_access_token(
            git_integration.get_installation(owner, repo_name).id
        ).token
    )

    repo = git_connection.get_repo(f"{owner}/{repo_name}")
    # If repo has config.json file in the Bot directory, use it. Otherwise, use the config.json file locally in the bot
    try:
        config_file = repo.get_contents("Bot/config.json")
        print("Using config file from the repository", flush=True)
        # Decode the file
        config = json.loads(base64.b64decode(config_file.content).decode("utf-8"))
    except:
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config = json.load(f)
                print("Using config file from the local Bot directory as it is not present in the repository", flush=True)
        else:
            print("ERROR: config.json not found! Please create it from config.json.example.", flush=True)
            abort(500)

    if payload_type == "issue_comment":
        return handle_issue_comment_event(repo, payload, config)
    elif payload_type == "issues":
        return handle_issue_creation_event(repo, payload, config)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)
