import os
import subprocess
import requests
from urllib.parse import urljoin

from subjective_abstract_data_source_package import SubjectiveDataSource
from brainboost_data_source_logger_package.BBLogger import BBLogger
from brainboost_configuration_package.BBConfig import BBConfig


class SubjectiveAzureDevOpsDataSource(SubjectiveDataSource):
    def __init__(self, name=None, session=None, dependency_data_sources=[], subscribers=None, params=None):
        super().__init__(name=name, session=session, dependency_data_sources=dependency_data_sources, subscribers=subscribers, params=params)
        self.params = params

    def fetch(self):
        organization = self.params['organization']
        project = self.params['project']
        target_directory = self.params['target_directory']
        token = self.params['token']

        BBLogger.log(f"Starting fetch process for Azure DevOps organization '{organization}' and project '{project}' into directory '{target_directory}'.")

        if not os.path.exists(target_directory):
            try:
                os.makedirs(target_directory)
                BBLogger.log(f"Created directory: {target_directory}")
            except OSError as e:
                BBLogger.log(f"Failed to create directory '{target_directory}': {e}")
                raise

        headers = {
            'Authorization': f'Basic {token}'
        }
        url = f"https://dev.azure.com/{organization}/{project}/_apis/git/repositories?api-version=6.0"

        BBLogger.log(f"Fetching repositories for Azure DevOps project '{project}'.")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            error_msg = f"Failed to fetch repositories: HTTP {response.status_code}"
            BBLogger.log(error_msg)
            raise ConnectionError(error_msg)

        repos = response.json().get('value', [])
        if not repos:
            BBLogger.log(f"No repositories found for project '{project}'.")
            return

        BBLogger.log(f"Found {len(repos)} repositories. Starting cloning process.")

        for repo in repos:
            clone_url = repo.get('remoteUrl')
            repo_name = repo.get('name', 'Unnamed Repository')
            if clone_url:
                self.clone_repo(clone_url, target_directory, repo_name)
            else:
                BBLogger.log(f"No clone URL found for repository '{repo_name}'. Skipping.")

        BBLogger.log("All repositories have been processed.")

    def clone_repo(self, repo_clone_url, target_directory, repo_name):
        try:
            BBLogger.log(f"Cloning repository '{repo_name}' from {repo_clone_url}...")
            subprocess.run(['git', 'clone', repo_clone_url], cwd=target_directory, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            BBLogger.log(f"Successfully cloned '{repo_name}'.")
        except subprocess.CalledProcessError as e:
            BBLogger.log(f"Error cloning '{repo_name}': {e.stderr.decode().strip()}")
        except Exception as e:
            BBLogger.log(f"Unexpected error cloning '{repo_name}': {e}")

    # ------------------------------------------------------------------
    def get_icon(self):
        """Return SVG icon content, preferring a local icon.svg in the plugin folder."""
        import os
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.svg')
        try:
            if os.path.exists(icon_path):
                with open(icon_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect width="24" height="24" rx="4" fill="#0078D7"/><path fill="#fff" d="M6 12l6-6 6 6-6 6z"/></svg>'

    def get_connection_data(self):
        """
        Return the connection type and required fields for Azure DevOps.
        """
        return {
            "connection_type": "AzureDevOps",
            "fields": ["organization", "project", "token", "target_directory"]
        }
