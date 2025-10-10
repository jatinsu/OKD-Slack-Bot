import os
import subprocess
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import threading
import time
import re
from dotenv import load_dotenv

# Initializes your app with your bot token and socket mode handler
load_dotenv()   
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
app = App(token=SLACK_BOT_TOKEN)

# Background 'goose' runner that runs alongside the Slack bot
def run_goose():
    print("running goose")
    try:
        result = subprocess.run([
            "goose",
            "run",
            "--no-session",
            "-t",
            (
                "grab the latest release in the 4-scos-next for OKD. "
                "If it's accepted, write a green check mark. If it's failed, give me a red x and then tell me the jobs that have failed. "
                "Do NOT run LatestAcceptedRelease or LatestRejectedRelease, only run LatestRelease."
                "AFTER running all your functions, wrap a summary in a <slack> tag. This will be used for parsing the output, so BE SURE to do this. "
                "Bold whether or not the release has been rejected or accepted within the slack tag. "
                "This is an example of the output:\n\n"
                "<slack>\n"
                "*OKD Release: <https://amd64.origin.releases.ci.openshift.org/releasetag/4.20.0-okd-scos.ec.0|4.20.0-okd-scos.ec.0>*\n"
                "*✅ Accepted*/*❌ Rejected**\n\n"
                "The following jobs have failed:\n\n"
                "- upgrade: <https://prow.ci.openshift.org/view/gs/test-platform-results/logs/release-openshift-okd-scos-installer-e2e-aws-upgrade-from-scos-next/xxxxxxxxxxxxxxx>\n"
                "</slack>\n"
            )
        ], capture_output=True, text=True)
        if result.stdout:
            os.makedirs("output", exist_ok=True)
            with open("output/OKD-release-output.txt", "w") as f:
                f.write(result.stdout.strip())

        if result.stderr:
            print(result.stderr.strip())
    except Exception as exc:
        print(f"goose runner error: {exc}")


def run_goose_with_prompt(prompt: str):
    print("running goose with custom prompt")
    with open("custom-prompt.txt", "r") as f:
        prompt_instructions = f.read()
    try:
        result = subprocess.run([
            "goose",
            "run",
            "--system", prompt_instructions,
            "--no-session",
            "-t",
            prompt
        ], capture_output=True, text=True)
        if result.stdout:
            with open("output/goose-prompt-output.txt", "w") as f:
                f.write(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())
        return result.stdout.strip() if result.stdout else ""
    except Exception as exc:
        print(f"goose runner error: {exc}")
        return ""


def scheduled_goose_messenger():
    while True:
        run_goose()
        if SLACK_CHANNEL_ID:
            try:
                with open("output/OKD-release-output.txt", "r") as f:
                    content = f.read()
                match = re.search(r"<slack>(.*?)</slack>", content, re.DOTALL)
                if match:
                    slack_message = match.group(1).strip()
                    app.client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=slack_message)
                else:
                    app.client.chat_postMessage(channel=SLACK_CHANNEL_ID, text="There was an error reading the OKD release output. Please try again.")
            except Exception as e:
                app.client.chat_postMessage(channel=SLACK_CHANNEL_ID, text=f"Error reading OKD release output: {e}")
        else:
            print("SLACK_CHANNEL_ID environment variable not set. Cannot post scheduled messages.")
        time.sleep(60)


@app.event("app_mention")
def handle_app_mention(body, say):
    print(f"App mention received: {body}")
    event = body["event"]
    text = event["text"]
    channel_id = event["channel"]
    prompt = re.sub(f"<@{app.client.auth_test()['user_id']}>", "", text).strip()
    if prompt:
        message_ts = say(f"Running goose with your prompt: {prompt}")
        message_ts = message_ts["ts"]
        goose_output = run_goose_with_prompt(prompt)
        if goose_output:
            match = re.search(r"<slack>(.*?)</slack>", goose_output, re.DOTALL)
            if match:
                slack_message = match.group(1).strip()
                # edit the loading results message to say the slack message
                app.client.chat_update(channel=channel_id, ts=message_ts, text=slack_message)
            else:
                say(text="Could not find a <slack> block in the output from your prompt.", channel=channel_id)
        else:
            say(text="Failed to run goose with your prompt.", channel=channel_id)
    else:
        say(text="Please provide a prompt after mentioning me. For example: `@botname summarize the latest OKD release`", channel=channel_id)


# Start your app
if __name__ == "__main__":
    # Start scheduled messenger in the background
    threading.Thread(target=scheduled_goose_messenger, daemon=True).start()
    
    SocketModeHandler(app, SLACK_APP_TOKEN).start()