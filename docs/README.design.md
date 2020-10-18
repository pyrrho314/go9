# Design Problem

The motivation for `go9` originated for me 30 years ago. Using CLI I always wanted a short special command to cd to various parts of the system. For example, I have various place I have to work, `gonovemdoc` would go to the novemdoc project, `gobin` would go to the bin project. This can't be done with little scripts in ~/bin b/c they can't change the local environment, running in a sub-environment.  And this is why you can't just write a nice command line tool in some other language like python as well. Except it turns out you can.

1. Originally I made aliases, because these run in the shell environment.
1. Then I had complications
   1. I wanted to be able to use different root directories
   1. I wanted a configurable system, there were too many directories
      in some projects, including all the systems directories, 
      that I needed to make more or less a bash command.
1. I was 'forced' to make a fairly complicated bash system and source it in my  
    `bash_profile` or `.bashrc`. Being in `bash` as a language, it was horrifying. It worked 
    but of course was not friendly to modify and extend.
1. I think at some point some of the alias commands were being generalized to 
   source in bash scripts in fragments, just to split things up in files.
1. One day it occurred to me I could source in the output of a python program
   if it output legal bash commands. 

So this is what `go9` does. A few top level aliases are sourced into .bashrc, and the go9 paths added with idempotent path manipulation scripts included in the package, so that the
go9.py program can programatically generate bash commands. This can be a little awkward, for example, producing output to the user requires using "echo" and some characters will get rendered in unexpected ways, whitespace changed, and the like.

### Roadmap

This tool has been pretty static as it long ago solved my desire to have a `go` command. I added the ability to run a command, mostly for commands I need just often enough to forget and have to research, so like a library of commands, like the one I used to reset audio in Ubuntu at one point. I have never gotten around to saving commands to run from history.  More pressing, it's Python2.7.
