from alfred5.client import SnippetClient


def test_snippets():
    client = SnippetClient()
    client.insert_snippet("This is a snippet", "Snippet Name", "keyword")
    client.package("Snippet Name", iconpath="icons/updated.png")
