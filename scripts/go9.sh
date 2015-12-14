#!/bin/bash
declare -A GO9_tt #target table

. nenv $* # SETS some useful environment variables

GO9_padding="                                                                    "

#GO9_tt[]=""
go9() {
    answer="$(go9.py $*)"
    eval "$answer"
}

go()
{
    answer="$(go9.py go $*)"
    eval "$answer"
}

# add exports for dirs
answer=$(go9.py direxports)
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
            case ${prev} in
                configure)
                    COMPREPLY=($(compgen -W "CM DSP NPU" ${cur}))
                    ;;
                show)
                    COMPREPLY=($(compgen -W "some other args" ${cur}))
                    ;;
            esac
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
complete -o filenames -o nospace -o bashdefault -F _comp_go9 go9
complete -o nospace -o bashdefault -F _comp_go go

