#  🎩 AlfredClient

Simplest Alfred Client that I use my own projects.

```bash
pip install alfred5
```

- Via `SnippetsClient` API create custom snippets programmaically
- Via `WorkflowClient` API create custom alfred workflow
    - Craete `requirements.txt` file for your python project to let `alfred5` installs them if needed 🙃
    - To install `from requirements.txt` do all import packages inside `main`
            - Use `global` keyword to access imported packages globally
        - `client.query` is the query string
        - `client.page_count` is the page count for pagination results
    - Dont need to add `alfred5` to `requirements.txt`
- Use `WorkflowClient.log` to log your message to alfred debugger 
    - [debugging alfred workflow](https://www.alfredapp.com/help/workflows/utilities/debug/)
    - [why this project use stderr for all logging operation](https://www.alfredforum.com/topic/14721-get-the-python-output-back-to-alfred/?do=findComment&comment=75303)
- Use `WorkflowClient(main, cache=True)` method to use caching system
    - Just do it for static (not timebased nor any dynamic stuff) response 
    - Db path is `db/results.yml` also you can see it from workflow debug panel

## ⭐️ Example Project

![alt](https://i.imgur.com/tUJjVUJ.png)

```python
from re import sub
from urllib.parse import quote_plus

from alfred5 import WorkflowClient


async def main(client: WorkflowClient):
    # To auto install requirements all import operation must be in here
    global get
    from requests import get

    query = client.query
    client.log(f"my query: {query}")  # use it to see your log in workflow debug panel

    # (use cache=True) Use cache system to quick response
    # if client.load_cached_response():
    #     return

    char_count = str(len( query))
    word_count = str(len(query.split(" ")))
    line_count = str(len(query.split("\n")))

    encoded_string = quote_plus(query)
    remove_dublication = " ".join(dict.fromkeys(query.split(" ")))

    upper_case = query.upper()
    lower_case = query.lower()
    capitalized = query.capitalize()
    template = sub(r"[a-zA-Z0-9]", "X", query)

    client.add_result(encoded_string, "Encoded", arg=encoded_string)
    client.add_result(remove_dublication, "Remove dublication", arg=remove_dublication)
    client.add_result(upper_case, "Upper Case", arg=upper_case)
    client.add_result(lower_case, "Lower Case", arg=lower_case)
    client.add_result(capitalized, "Capitalized", arg=capitalized)
    client.add_result(template, "Template", arg=template)
    client.add_result(char_count, "Characters", arg=char_count)
    client.add_result(word_count, "Words", arg=word_count)
    client.add_result(line_count, "Lines", arg=line_count)
    
    # (use cache=True) to cache result for query (if u work with static results (not dynamic; coin price etc.))
    # client.cache_response()  

if __name__ == "__main__":
    WorkflowClient.run(main)  # WorkflowClient.run(main, cache=True)

```


## 🔰 How to Create Workflow

![insturaction1](https://i.imgur.com/2oDMChr.png)
![insturaction2](https://i.imgur.com/IMVWNDm.png)
![insturaction3](https://i.imgur.com/WicJKBN.png)
![insturaction4](https://i.imgur.com/AwPNT8Y.png)


## 🪪 License

```
Copyright 2023 Yunus Emre Ak ~ YEmreAk.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
