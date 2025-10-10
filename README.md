# OKD Slack Bot
## Setup
1. make sure to clone [the release controller repo](https://github.com/jatinsu/releasecontroller-mcp-server) and run through the steps to build and install 
2. go to [your slack api dashboard](https://api.slack.com/apps) to grab your
    1. SLACK_BOT_TOKEN
    2. SLACK_APP_TOKEN
    3. SLACK_CHANNEL_ID (you can find this by right clicking the slack channel, view channel detials, and scroll down)

    and put it in a file named `.env`
3. create a enviorment through `python -m venv venv` and run `source venv/bin/activate`
4. run `pip install -r requirements.txt` to install the dependencies

## Running
1. From the directory where the release controller repo was cloned, run `./releasecontroller-mcp-server --sse-port 8080`
2. Go back to directory where you cloned this repo and run `python app.py` to start up the app
