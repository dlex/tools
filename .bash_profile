#!bash

alias gs='git status'
alias go='git merge origin/`git rev-parse --abbrev-ref HEAD` --ff-only -q'
alias gp='git pull -q; git submodule update'
alias gu='git push --set-upstream origin `git rev-parse --abbrev-ref HEAD`'
alias gbn='git branch -v --no-merge origin/master --sort=-committerdate'
alias gsu='git submodule update'
alias gf='git fetch -q'

# 'git grep rev-list'; ggr <expression> <path>
ggr() {
  git rev-list --all -- $2 | xargs -I{} git grep $1 {} -- $2
}

# 'TortoiseGit'; "tg help" and look for TortoiseGitProc in it for syntax
tg() {
  if [[ -z "$1" ]]; then
    echo "syntax: tg <command> [<path>]"
    echo "commands: help bisect fetch log commit add revert cleanup resolve switch merge remove rename diff showcompare conflicteditor repostatus repobrowser ignore blame pull push rebase stashsave stashapply stashpop subadd subupdate subsync reflog refbrowse revisiongraph tag"
    echo "more commands: clone repocreate export settings cat daemon pgpfp"
    return 1
  fi
  "/c/Program Files/TortoiseGit/bin/TortoiseGitProc.exe" "//command:$1" "//path:${2:-.}"
}

export GIT_PS1_SHOWUPSTREAM=verbose
