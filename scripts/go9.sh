#!/bin/bash
declare -A GO9_tt #target table

. nenv $* # SETS some useful environment variables

GO9_padding="                                                                    "

#GO9_tt[]=""
go9() {
    argline=""
    for arg in "$@"
    do
      numwrds=$(echo "$arg" | wc -w)
      if [ "$numwrds" -gt 1 ]
      then
        argline=$argline" \"$arg\""
      else
        argline=$argline" $arg"
      fi
      let "index+=1"
    done             # $@ sees arguments as separate words. 
    #echo $argline
    answer="$(go9.py $argline)"
    eval "$answer"
}
export -f go9
run()
{
    answer="$(go9.py run $*)"
    eval "$answer"
}
export -f run

go()
{
    answer="$(go9.py go $*)"
    eval "$answer"
}
export -f go

thisis()
{
    answer="$(go9.py add $*)"
    eval "$answer"
}
export -f thisis

# add exports for dirs
answer=$(go9.py exportdirs)
eval "$answer"

GO9_subcmds=$(go9.py listcmds export)
GO9_go_targets=$(go9.py gotargets export)
_comp_go9()
{
local cur prev
    #COMP_WORDS
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}

    case ${COMP_CWORD} in
        1)
            # echo "in comp func" $GO9_subcmds
            COMPREPLY=($(compgen -W "$GO9_subcmds" ${cur}))
            ;;
        2)
            words=$(go9.py --export listsubcmds ${prev})
            COMPREPLY=($(compgen -W "$words" ${cur}))
            ;;
        *)
            COMPREPLY=()
            ;;
    esac
}
_comp_go()
{
local cur prev
    #COMP_WORDS
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}

    case ${COMP_CWORD} in
        1)
            # echo "in comp func" $GO9_subcmds
            COMPREPLY=($(compgen -W "$GO9_go_targets" ${cur}))
            ;;
        *)
            COMPREPLY=()
            ;;
    esac
}

_comp_run()
{
    local cur prev
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}
    case ${COMP_CWORD} in
        1)
            # echo "in comp func" $GO9_subcmds
            runtargs=$(go9.py --export runcmds )
            COMPREPLY=($(compgen -W "$runtargs" ${cur}))
            ;;
        2)
            words=$(go9.py --export listsubcmds ${prev})
            COMPREPLY=($(compgen -W "$words" ${cur}))
            ;;
        *)
            COMPREPLY=()
            ;;
    esac
}
complete -o filenames -o nospace -o bashdefault -F _comp_go9 go9
complete -o nospace -o bashdefault -F _comp_go go
complete -o nospace -o bashdefault -F _comp_run run

