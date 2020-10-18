# go9
Tool for bash that helps move around development space. Requires only python.

## Installation
### Idea

0. You need the go9 scripts directory with go9.sh and go9.py in PATH
1. you need the python utility directory (with go9util) in PYTHONPATH
2. you will need to source go9.sh since it modifies your extant environment

### Instructions

Clone the repository into $HOME/tools, e.g.:
```
cd $HOME
mkdir go9
cd go9
git clone https://github.com/pyrrho314/go9.git
```

Then add the following to
.bashrc:

```
# go9
. $HOME/tools/go9/scripts/addpath $HOME/tools/go9/scripts
. addpypath $HOME/tools/go9/py

. go9.sh
```

NOTE: If you put go9 elsewhere, make the nec. alterations to the above `.bashrc` lines. The programs `addpath` and `addpypath` will idempotently add paths to PATH and PYTHONPATH respectively.

NOTE: addpath and addpypath are idempotent so they won't keep adding themselves to the path when called repeatedly (i.e. in a subshell).

## To Use

Sourcing go9.sh adds two bash function to the environment, 'go' and 'go9'.  Use `go9 add \<this_dir_alias\>` when in the target directory, then `go \<target_dir_alias\>` to cd to that directory.  If you type 'go' with no argument, a list of available directories is displayed. Type `go9 help` for help.

## Windows Support

Windows support is not complete, though `go9 add xyz` add and `go xyz` have been made to work, there are other oddities, 
commands probably do not work, environment export doesn't work, due to some assumptions about unix filenames.


