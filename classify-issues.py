import os
import openai
import json

# Setup OpenAPI configuration and models
## Configure OpenAI
openai.organization = os.getenv("OPENAI_ORG_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")
## Model to use
model = "gpt-3.5-turbo"
#model = "text-davinci-003"
## Issues files
issues_file = "issues.json"

# Load issues
issues = None
with open(issues_file, 'r') as f:
    issues = json.load(f)

## What output do we want from the issue and comments?
## - Number
## - Title
## - Summary
## - Sentiment
## - Proposed classification



def sanitizeInput(input):
    return input.replace("\r", " ").replace("\n", " ")

def classify_issue(issue):
    number = issue["number"]
    title = issue["title"]
    system = """In this task, you will act as an AI assistant analyzing a GitHub issue discussion, including the issue's body and comments. Your output should be a JSON object containing the following items: summary, sentiment, and labels. The summary should provide an overview of the issue, sentiment should reflect the overall emotions or feelings expressed in the discussion, and labels should include relevant categories to help project organizers understand the issue's components.

Example discussion:
Issue: "Unconfirmed transactions due to low fee rate"
Body: "I recently tried sending a transaction with a low fee rate, and it has been unconfirmed for over 24 hours. Can someone help me figure out what's going on?"
Comment 1: "This happens sometimes when the network is congested. Try using a higher fee rate next time."
Comment 2: "You can try using a transaction accelerator to speed it up."
Comment 3: "It's always best to check the recommended fee rates before sending a transaction."

Your response should look like this:
{"summary": "User is experiencing issues with unconfirmed transactions due to small fee rate", "sentiment": "cheerful", "labels": ["wallet", "user-support"]}"
"""

    reactionGroups = {}
    totalCount = 0
    for reaction in issue["reactionGroups"]:
      count = int(reaction["users"]["totalCount"])
      if reaction["content"] in reactionGroups:
        reactionGroups[reaction["content"]] += count
      else:
        reactionGroups[reaction["content"]] = count
      totalCount += count

    summary = sanitizeInput("Title: \"" + sanitizeInput(issue["title"])) + "\"\n"
    summary += sanitizeInput("Body: \"" + sanitizeInput(issue["body"])) + "\"\n"
    i=0
    for comment in issue["comments"]:
        summary += sanitizeInput("Comment" + str(i) + " :" + sanitizeInput(comment["body"])) + "\n"
        for reaction in comment["reactionGroups"]:
          count = int(reaction["users"]["totalCount"])
          if reaction["content"] in reactionGroups:
            reactionGroups[reaction["content"]] += count
          else:
            reactionGroups[reaction["content"]] = count
          totalCount += count
        i+=1
    try:
      oAIRet = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": summary}]
      )
    except:
      print("Error calling OpenAI for %d" % (number))
      return {"number": number, "title": title.strip(), "summary": summary.strip(), "reactionGroups": reactionGroups}
    if len(oAIRet["choices"]) > 0:
      summary = oAIRet["choices"][0]["message"]["content"]
    return {"number": number, "title": title.strip(), "summary": summary.strip(), "reactionGroups": reactionGroups, "totalCount": totalCount}

if __name__ == "__main__":
  i=0
  classifiedIssues = []
  for i in range(len(issues)):
    classifiedIssue = classify_issue(issues[i])
    print(classifiedIssue)
    try:
      classifiedIssue["summaryJson"] = json.loads(classifiedIssue["summary"])
    except:
      print("Error parsing JSON for %d" % (i))
    classifiedIssues.append(classifiedIssue)
  with open('classifiedIssue.json', 'w') as outfile:
    json.dump(classifiedIssues, outfile)
