import re
from collections import namedtuple
import sublime


Branch = namedtuple("Branch", (
    "name",
    "remote",
    "name_with_remote",
    "commit_hash",
    "commit_msg",
    "tracking",
    "tracking_status",
    "active",
    "description"
))


class BranchesMixin():

    def get_branches(self, sort_by_recent=False):
        """
        Return a list of all local and remote branches.
        """
        stdout = self.git(
            "branch", "-a", "-vv", "--no-abbrev", "--no-color", "--sort=-committerdate" if sort_by_recent else None)
        return (branch
                for branch in (self._parse_branch_line(self, line) for line in stdout.split("\n"))
                if branch)

    @staticmethod
    def _parse_branch_line(self, line):
        line = line.strip()
        if not line:
            return None

        branch = r"([a-zA-Z0-9\-\_\/\.\-\u263a-\U0001f645]+(?<!\.lock)(?<!\/)(?<!\.))"
        pattern = r"(\* )?(remotes/)?" + branch + r" +([0-9a-f]{40}) (\[([a-zA-Z0-9\-\_\/\.]+)(: ([^\]]+))?\] )?(.*)"

        match = re.match(pattern, line)
        if not match:
            return None

        (is_active,
         is_remote,
         branch_name,
         commit_hash,
         _,
         tracking_branch,
         _,
         tracking_status,
         commit_msg
         ) = match.groups()

        active = bool(is_active)
        remote = branch_name.split("/")[0] if is_remote else None

        savvy_settings = sublime.load_settings("GitSavvy.sublime-settings")
        enable_branch_descriptions = savvy_settings.get("enable_branch_descriptions")

        hide_description = is_remote or not enable_branch_descriptions
        description = "" if hide_description else self.git(
            "config",
            "branch.{}.description".format(branch_name),
            throw_on_stderr=False
        ).strip("\n")

        return Branch(
            "/".join(branch_name.split("/")[1:]) if is_remote else branch_name,
            remote,
            branch_name,
            commit_hash,
            commit_msg,
            tracking_branch,
            tracking_status,
            active,
            description
        )

    def merge(self, branch_names):
        """
        Merge `branch_names` into active branch.
        """

        self.git("merge", *branch_names)

    def get_local_branch(self, branch_name):
        """
        Get a local Branch tuple from branch name.
        """
        for branch in self.get_branches():
            if not branch.remote and branch.name == branch_name:
                return branch

    def branches_containing_commit(self, commit_hash, local_only=True, remote_only=False):
        """
        Return a list of branches which contain a particular commit.
        """
        branches = self.git(
            "branch",
            "-a" if not local_only and not remote_only else None,
            "-r" if remote_only else None,
            "--contains",
            commit_hash
            ).strip().split("\n")
        return [branch.strip() for branch in branches]
