from typing import Dict
import os 

from .plugin import Plugin

from github import Github
from github import Auth

class GithubPlugin(Plugin):
    """
    A plugin to control github 
    """
    def __init__(self):
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            raise ValueError('GITHUB_TOKEN environment variable must be set to use GithubPlugin')
        self.github_token = github_token
        auth = Auth.Token(self.github_token)
        self.g = Github(auth=auth)
        self.repos_cache = []

    def get_source_name(self) -> str:
        return "Github"

    def get_spec(self) -> [Dict]:
        return [{
            "name": "get_repos",
            "description": "Get filtered or, if no query provided, all repositories from github",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Part(s) of the repository name to filter by"}
                },
                #"required": ["query"]
            }
        },
        {
            "name": "get_prs",
            "description": "Get repository pull requests (prs)",
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {"type": "string", "description": "The exact name of the repository"}
                },
                "required": ["repository"]
            }
        },
        {
            "name": "merge_pr",
            "description": "Merge a pull request (pr) by exact repository name and number",
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {"type": "string", "description": "The exact name of the repository"},
                    "number": {"type": "number", "description": "The number of the pull request to merge"}
                },
                "required": ["repository"]
            }
        }]

    async def execute(self, function_name, **kwargs) -> Dict:
        if len(self.repos_cache) == 0: 
                print('Starting caching repositories')
                for repo in self.g.get_user().get_repos(): 
                    self.repos_cache.append(repo)
                print('Done caching repositories')

        if function_name == 'merge_pr':
            # find the repository 
            repo_name = kwargs['repository'].lower()
            pr_number = int(kwargs['number'])
            for repo in self.repos_cache:
                if repo.name.lower() == repo_name:
                    # find the pr
                    for pr in repo.get_pulls():
                        if pr.number == pr_number:
                            pr.merge()
                            return {'message': 'PR merged'}
                    return {'message': 'PR not found'}
            return {'message': 'Repository not found'}

        if function_name == 'get_prs':
            # find the repository 
            repo_name = kwargs['repository'].lower()
            for repo in self.repos_cache:
                if repo.name.lower() == repo_name:
                    prs = []
                    for pr in repo.get_pulls():
                        prs.append({'title': pr.title, 'body': pr.body, 'url': pr.html_url,'number': pr.number})
                    return prs

        if function_name == 'get_repos':
            
            # get the query from kwargs and split it by space;
            # then, for each word in the query, find all repos that contain all the words 
            # in the query
            query = kwargs['query']
            repos = [] 
            if query:
                repos = []
                for repo in self.repos_cache:
                    hit = True
                    lname = repo.name.lower()
                    for word in query.split(' '):
                        if not word.lower() in lname:
                            hit = False
                            break
                    if hit:
                        # append an object with the name, description and url; 
                        # this is what the bot will return to the user
                        repos.append({'name': repo.name, 'description': repo.description, 'url': repo.html_url})
                return repos
            # if no query is provided, return all repos
            else:
                for repo in self.repos_cache:
                    repos.append({'name': repo.name, 'description': repo.description, 'url': repo.html_url})

                return repos
            
            
            