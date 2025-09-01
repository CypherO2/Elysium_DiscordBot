# Elysium Discord Bot Contributing Guidelines
Welcome to the contributing guideline document for the Elysium Discord Bot!

> [!WARNING]
> To begin contributing you must first understand the project goals and what needs doing, if you haven't already, please have a read of our [README](README.md) where the project is discussed in more detail.

The details covered in this CONTRIBUTING document will cover linting, formatting, project structure and various other general requirements and standards that need to kept so that the code is:

1. Well Formatted
2. Readable
3. Simple to go into and repair
4. Easy to update
5. Follows all appropriate naming conventions.

## Pull Requests

When writing as Pull Request(PR), you should be mindful of the task you have completed, keep an eye on the commit messages you have used on your branch and ask yourself: does this accurately demonstrate what I have changed? This ensures the reviewer has clear context of what has been changed

Additionally, please make sure that each PR has at least one authored comment that explains what the PR is about/ does.

- The `chore/` tag is to be used at the front of pull request titles (e.g. `chore/Branch-Name`) when the branch being merged doesn't make any significant changes to the codebase, such as when you update a readme or rearrange files or even when you re-format code.
- The `fix/` tag is to be used at the front of pull request titles (e.g. `fix/Fix-Name`) when the branch being merged is something that doesn't add to the solution but rather fixes an existing bug or flaw in the codebase/ program.
- The `feat/` tag is to be used at the front of pull request titles (e.g. `feat/Feature-Name`) when a branch being merged is in relation to a new feature being added to the program.
- The `test/` tag is to be used at the front of pull request titles (e.g. `test/Test-name`) when the branch being merged is adding and/or running a test within the program's codebase.
- The `perf/` tag is to be used at the front of pull request titles (e.g. `perf/performance-fix`) when the branch being merged is making improvements for the sake of performance.

## Branch Names

- The `chore/` tag is to be used at the front of branch names (e.g. `chore/Branch-Name`) when the task you are carrying out doesn't make any significant changes to the codebase, such as when you update a readme or rearrange files or even when you re-format code.
- The `fix/` tag is to be used at the front of branch names (e.g. `fix/Fix-Name`) when the change to the code is something that doesn't add to the solution but rather fixes an existing bug or flaw in the codebase/ program.
- The `feat/` tag is to be used at the front of branch names (e.g. `feat/Feature-Name`) when a new feature or functionality has been added to the program.
- The `test/` tag is to be used at the front of branch names (e.g. `test/Test-name`) while adding or running a test within the program's codebase.
- The `perf/` tag is to be used at the front of branch names (e.g. `perf/performance-fix`) when making improvements for the sake of performance.

### Commit Messages

- The `chore:` tag is to be used at the front of a commit message (e.g. `chore: Cleaned up/Updated/Moved/Formatted XXXX`) when the task you are carrying out doesn't make any significant changes to the codebase, such as when you update a readme or rearrange files or even when you re-format code.
- The `fix:` tag is to be used at the front of a commit message (e.g. `fix: changed XXXX while trying to fix XXXX`) when the change to the code is something that doesn't add to the solution but rather fixes an existing bug or flaw in the codebase/ program.
- The `feat:` tag is to be used at the front of a commit message (e.g. `feat: created/added/edited/moved/merged XXXX while implementing XXXX`) while adding a new feature or functionality to the program.
- The `test:` tag is to be used at the front of a commit message (e.g. `test: created test for XXXX to ensure XXXX`) while adding or running a test in the program's codebase.
- The `perf:` tag is to be used at the front of a commit message (e.g. `perf: added/removed/changes XXXX to improve performance by XX%`) when making changes to the codebase for the sake of performance.

## Issues

Issues are used for two reasons:

1. you have a task you wish to assign to someone and/or an issue to report
2. you have a task you yourself wish would be completed and are endeavouring to do it yourself.

When reporting an issue for others please be mindful of what the issue is reporting and attach as much context as you can.

This can include screenshots, in-depth descriptions of the issue / task and the use of the following issue tags when reporting an Issue, this is so that we can categorise them more effectively:

- The `Chore/` tag is to be used at the front of a issue title (e.g. `Chore/BranchName`) when the task you are requesting is something that would not effect the solution significantly, such as requesting an update to README.md
- The `Bug/` tag is to be used at the front of a issue title (e.g. `Bug/Bug Name`) when the issue is reporting a bug that requires a fix.
- The `Feat/` tag is to be used at the front of a issue title (e.g. `Feat/Feature Name`) when a new feature or functionality is being requested.
- The `Test/` tag is to be used at the front of a issue (e.g. `Test/Test Name`) while requesting the addition of tests for specific features, fixes or bugs.
- The `Perf/` tag is to be used at the front of an issue (e.g. `Perf/Performance Fix`) while requesting or reporting a performance related fix/ issue

## Linting and Formatting

When working on this project we would prefer for people to use the following Linting/ Formatting extensions:

- **Pylint**: Linting support for Python files.
- **Trunk Code Quality**: Automated Code Quality for Teams: universal formatting, linting, static analysis, and security
- **Ruff**: An extremely fast Python linter and code formatter, written in Rust.
- **MyPy**: Type checking support for Python files.
- **Black**: Formatting support for Python files.

## Project Structure

The project is important to maintain as it is how we will be able to consistently reference places in the code in both documentation and other places in the code itself, for example:

```txt
elysium_discordbot/            # root of the project
├── assets/                    # folder when all assets, that are not external links, are to be stored
└── elysium-bot/               # bot code
    ├── cogs                   # cogs folder
    │   ├── twitchcog.py       # cog governing the twitch aspects of the bot
    │   ├── utilitycog.py      # cog governing the utility aspects of the bot
    │   ├── yt-musiccog.py     # cog governing the music player aspect of the bot
    │   └── moderationcog.py   # cog governing the moderation aspect of the bot
    ├── main.py                # primary python file from which the bot is initialised
    ├── config.json            # config file for bot configuration
    └── functions.py           # additional python function file
```

### Naming Conventions

Finally, keep in mind that this is a community project and as such should have naming conventions that reflect that, make sure that the constants, variable and function names along with file names are clear and concise so as to allow other to work with your code.
