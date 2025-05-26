from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool
from datetime import datetime
from openai import OpenAI
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
import os.path
import json


SPREADSHEET_ID="1zPqbK86GzbkZ3G9V6fajrWpghz7GP10BnaIJl-D_FYw"
RANGE_NAME='C:C'
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

#SETUP
def sheetsApiSetup():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())
    return creds


def read_google_sheet(range_name:str):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = sheetsApiSetup()

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SPREADSHEET_ID, range=range_name)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            return None

        return values
    except HttpError as err:
        return err.content

# determine_category_tool = Tool(
#     name="determine_category",
#     func = read_google_sheet,
#     description="Determine the distinct spending category for a purchase from a Google Sheet, first checking the currently existing categories. No need to enter any arguments."
# )


def write_to_google_sheet(range_name:str, _values:list[list[str]]):
    # creds, _ = google.auth.default()
    # pylint: disable=maybe-no-member
    creds= sheetsApiSetup()

    try:
        service = build("sheets", "v4", credentials=creds)
        values = _values
        body = {"values": values}

        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )

        print(f"{result.get('updatedCells')} cells updated.")
        return result

    except HttpError as error:
        print(f"An error occurred: {error}")
        return error
    
    
def handle_expenses(json_input: str):
    # Accepts a JSON string or dict from the parser tool
    data = json.loads(json_input)

    results = []
    if isinstance(data, list):
        for purchase in data:
            result = add_expense_from_json(purchase)
            results.append(result)
    else:
        result = add_expense_from_json(data)
        results.append(result)
    return results

def add_expense_from_json(json_str: str):
    # Accepts a JSON string or dict from the parser tool
    if isinstance(json_str, dict):
        data = json_str
    else:
        data = json.loads(json_str)
    # Map fields to columns as needed
    # Example: date, amount, category, description
    from datetime import date
    today = date.today().isoformat()
    row = [
        data.get("date", today),
        data["amount"],
        data.get("currency", "USD"),
        data.get("category", ""),
        data.get("description", "")
    ]
    # Find next available row
    # creds = sheetsApiSetup()
    # service = build("sheets", "v4", credentials=creds)
    # result = service.spreadsheets().values().get(
    #     spreadsheetId=SPREADSHEET_ID, range="A:A"
    # ).execute()
    # values = result.get("values", [])
    values = read_google_sheet("A:A")
    
    next_row = len(values) + 1
    range_name = f"A{next_row}:E{next_row}"
    return write_to_google_sheet(range_name, [row])

add_expense_tool = Tool(
    name="add_expense",
    func=handle_expenses,
    description="Add the provided expenses to the Google Sheet. Input should be a JSON string with fields: amount, currency, category, description, date. Can be more than one expense."
)
    